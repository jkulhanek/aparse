from typing import Type
from .core import Handler, AllArguments, ParameterWithPath, Runtime, _empty
from ._lib import register_handler, preprocess_parameter
from .utils import get_parameters
from .utils import prefix_parameter, merge_parameter_trees


@register_handler
class DefaultHandler(Handler):
    def preprocess_parameter(self, param: ParameterWithPath):
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

    def add_parameter(self, param, runtime: Runtime):
        if len(param.children) > 0 or param.argument_type not in {str, float, bool, int}:
            return True

        argument_name = param.argument_name
        if param.argument_type == bool:
            negative_option = argument_name
            if negative_option.startswith('use-'):
                negative_option = negative_option[len('use-'):]
            argument_name += '/' + f'--no-{negative_option}'
        required = param.default_factory is None
        runtime.add_parameter(param.argument_name, param.argument_type,
                              required=required, help=param.help,
                              default=param.default if param.default_factory is not None else _empty,
                              choices=param.choices)
        return True


@register_handler
class AllArgumentsHandler(Handler):
    def add_parameter(self, param, runtime, *args, **kwargs):
        if param.type == AllArguments:
            return True
        return False

    def bind(self, param, args, children):
        if param.type == AllArguments:
            value = {k: v for k, v in args.items() if k != '_aparse_parameters'}
            return True, value
        return False, args

    def preprocess_parameter(self, param):
        if param.type == AllArguments:
            return True, param.replace(argument_type=AllArguments, children=[])
        return False, param


@register_handler
class SimpleListHandler(Handler):
    def _list_type(self, tp: Type):
        if getattr(tp, '__origin__', None) == list:
            tp = tp.__args__[0]
            if tp in (int, str, float):
                return tp
        return None

    def preprocess_parameter(self, parameter):
        if self._list_type(parameter.type) is not None:
            return True, parameter.replace(argument_type=str)
        return False, parameter

    def parse_value(self, parameter, value):
        list_type = self._list_type(parameter.type)
        if list_type is not None and isinstance(value, str):
            return True, list(map(list_type, value.split(',')))
        return False, value


@register_handler
class FromStrHandler(Handler):
    def _does_handle(self, tp: Type):
        return hasattr(tp, 'from_str')

    def preprocess_parameter(self, parameter):
        if self._does_handle(parameter.type):
            return True, parameter.replace(argument_type=str)
        return False, parameter

    def parse_value(self, parameter, value):
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

    def preprocess_parameter(self, parameter):
        if self._does_handle(parameter.type):
            return True, parameter.replace(
                argument_type=str,
                choices=list(parameter.type.__conditional_map__.keys()))
        return False, parameter

    def before_parse(self, root, parser, kwargs):
        result = []
        for param in root.enumerate_parameters():
            if self._does_handle(param.type):
                key = kwargs.get(param.argument_name, param.default)
                tp = param.type.__conditional_map__.get(key, None)
                if tp is not None:
                    parameter = get_parameters(tp).walk(preprocess_parameter)
                    parameter = parameter.replace(name=param.name, type=tp)
                    if not param.type.__conditional_prefix__:
                        parameter = parameter.replace(_argument_name=(None,))
                    if param.parent is not None and param.parent.full_name is not None:
                        parameter = prefix_parameter(parameter, param.parent.full_name)
                    result.append(parameter)
        if len(result) > 0:
            result = merge_parameter_trees(*result)
            return result
        return None

    def after_parse(self, root, argparse_args, kwargs):
        for param in root.enumerate_parameters():
            if ConditionalTypeHandler._does_handle(param.type):
                pass
        return kwargs
