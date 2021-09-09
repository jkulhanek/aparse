import inspect
import dataclasses
from typing import Type, Any, Tuple
from .core import Handler, Parameter, ArgparseArguments, ParameterWithPath
from ._lib import register_handler, get_parameters, preprocess_argparse_parameter
from .utils import get_path, prefix_parameter, merge_parameter_trees


@register_handler
class DefaultHandler(Handler):
    def preprocess_argparse_parameter(self, param: ParameterWithPath):
        if len(param.children) > 0:
            return True, param.parameter
        if param.type is None:
            return True, None

        choices = None
        meta_name = getattr(getattr(param.type, '__origin__', None), '_name', None)
        default = param.default_factory() if param.default_factory is not None else None
        arg_type = None
        if meta_name == 'Literal':
            arg_type = type(param.type.__args__[0])
            choices = param.type.__args__
        elif meta_name == 'Union':
            tp = set((x for x in param.type.__args__ if not isinstance(None, x)))
            if str in tp:
                arg_type = str
            if int in tp:
                arg_type = int
            if float in tp:
                arg_type = float
        elif hasattr(param.type, 'from_str') and callable(param.type.from_str):
            arg_type = str
        elif param.type in [int, float, str, bool]:
            arg_type = param.type
        elif isinstance(default, bool):
            arg_type = bool
        if arg_type is not None:
            return True, param.replace(argument_type=arg_type, choices=choices)
        return False, None

    def add_argparse_arguments(self, param, parser, existing_action=None):
        if len(param.children) > 0 and param.type not in {str, float, bool, int}:
            return True, parser

        required = param.default_factory is None
        if existing_action is not None:
            # We will update default
            existing_action.required = required
            existing_action.help = f'{param.help} [{param.default}]' if not required else f'{param.help} [required]'
            existing_action.choices = param.choices
            parser.set_defaults(**{param.argument_name: param.default})
        else:
            arg_type = param.argument_type
            arg_name = param.argument_name.replace('_', '-')
            if arg_type == bool:
                parser.set_defaults(**{param.argument_name: param.default})
                parser.add_argument(f'--{arg_name}', dest=param.argument_name, action='store_true', help=f'{param.help} [default]' if param.default_factory() else param.help)
                _arg_name = arg_name
                if arg_name.startswith('use-'):
                    _arg_name = arg_name[len('use-'):]
                parser.add_argument(f'--no-{_arg_name}', dest=param.argument_name, action='store_false', help=f'{param.help} [default]' if not param.default_factory() else param.help)
            else:
                if param.default_factory is not None:
                    parser.add_argument(f'--{arg_name}', type=arg_type, choices=param.choices, default=param.default, help=f'{help} [{param.default}]')
                else:
                    parser.add_argument(f'--{arg_name}', type=arg_type, choices=param.choices, default=param.default, required=True, help=f'{help} [required]')
        return True, parser


@register_handler
class ArgparseArgumentsHandler(Handler):
    def add_argparse_arguments(self, param, parser, *args, **kwargs):
        if param.type == ArgparseArguments:
            return True, parser
        return False, parser

    def bind(self, param, args, children):
        if param.type == ArgparseArguments:
            value = {k: v for k, v in args.__dict__.items() if k != '_aparse_parameters'}
            return True, value
        return False, args

    def preprocess_argparse_parameter(self, param: Parameter) -> Tuple[bool, Parameter]:
        if param.type == ArgparseArguments:
            return True, param.replace(argument_type=ArgparseArguments, children=[])
        return False, param


@register_handler
class SimpleListHandler(Handler):
    def _list_type(self, tp: Type):
        if getattr(tp, '__origin__', None) == list:
            tp = tp.__args__[0]
            if tp in (int, str, float):
                return tp
        return None

    def preprocess_argparse_parameter(self, parameter: Parameter) -> Type:
        if self._list_type(parameter.type) is not None:
            return True, parameter.replace(argument_type=str)
        return False, parameter

    def parse_value(self, parameter: Parameter, value: Any) -> Any:
        list_type = self._list_type(parameter.type)
        if list_type is not None and isinstance(value, str):
            return True, list(map(list_type, value.split(',')))
        return False, value


@register_handler
class FromStrHandler(Handler):
    def _does_handle(self, tp: Type):
        return hasattr(tp, 'from_str')

    def preprocess_argparse_parameter(self, parameter: Parameter) -> Type:
        if self._does_handle(parameter.type):
            return True, parameter.replace(argument_type=str)
        return False, parameter

    def parse_value(self, parameter: Parameter, value: Any) -> Any:
        if self._does_handle(parameter.type) and isinstance(value, str):
            return True, parameter.type.from_str(value)
        return False, value


@register_handler
class ConditionalTypeHandler(Handler):
    @staticmethod
    def _does_handle(tp: Type):
        meta_name = getattr(getattr(tp, '__origin__', None), '_name', None)
        if meta_name == 'Union':
            return hasattr(tp, '__conditional_map__')
        return False

    def preprocess_argparse_parameter(self, parameter: Parameter) -> Type:
        if self._does_handle(parameter.type):
            return True, parameter.replace(
                argument_type=str,
                choices=list(parameter.type.__conditional_map__.keys()))
        return False, parameter

    def before_parse(self, root, parser, kwargs):
        result = []
        for param in root.enumerate_parameters():
            if self._does_handle(param.type):
                assert param.argument_name in kwargs
                key = kwargs[param.argument_name]
                tp = param.type.__conditional_map__.get(key, None)
                if tp is not None:
                    parameter = get_parameters(tp).walk(preprocess_argparse_parameter)
                    parameter = parameter.replace(name=param.name, type=tp)
                    if param.parent is not None and param.parent.full_name is not None:
                        parameter = prefix_parameter(parameter, param.parent.full_name)
                    result.append(parameter)
        if len(result) > 0:
            result = merge_parameter_trees(*result)
            return result
        return None

    def after_parse(root, argparse_args, kwargs):
        for param in root.enumerate_parameters():
            if ConditionalTypeHandler._does_handle(param.type):
                pass
