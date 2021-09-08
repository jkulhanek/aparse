import inspect
import sys
from functools import partial
from collections import OrderedDict
from argparse import ArgumentParser, Namespace
from typing import List, Dict, Any, Set, Callable, Optional
import dataclasses
from .core import Parameter


handlers = []


def register_handler(handler):
    handlers.insert(0, handler())
    return handler


def ignore_parameters(parameters, ignore):
    def _call(x, children):
        if x.full_name in ignore:
            return None
        return dataclasses.replace(x, children=children)
    return parameters.walk(_call)


def get_parameters(obj):
    generated = set()
    root = Parameter(name=None, type=dict)

    def collect_parameters(cls, parent=None):
        parameters = inspect.signature(cls.__init__).parameters
        calls_parent = False
        for p in parameters.values():
            if p.name == 'self':
                continue
            if p.kind == inspect.Parameter.VAR_KEYWORD:
                for base in cls.__bases__:
                    calls_parent = True
            if p.kind == inspect.Parameter.KEYWORD_ONLY or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                full_name = f'{parent.full_name}.{p.name}'
                assert full_name not in generated, f'{full_name} was already generated'
                default_factory = None
                if p.default != p.empty:
                    default_factory = lambda: p.default
                elif dataclasses.is_dataclass(cls) and isinstance(p.default, dataclasses._HAS_DEFAULT_FACTORY_CLASS):
                    default_factory = cls.__dataclass_fields__[p.name].default_factory
                param = Parameter(p.name, p.annotation, default_factory=default_factory, parent=parent)
                generated.add(param.full_name)
                if dataclasses.is_dataclass(p.annotation):
                    param.children.extend(collect_parameters(p.annotation, parent=param))
                yield param
        if calls_parent:
            for p in collect_parameters(base, parent):
                yield p

    if inspect.isclass(obj):
        params = list(collect_parameters(obj, root))
    else:
        params = []
        parameters = inspect.signature(obj).parameters
        for p in parameters.values():
            if p.kind == inspect.Parameter.KEYWORD_ONLY or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                default_factory = None
                if p.default != p.empty:
                    default_factory = lambda: p.default
                param = Parameter(
                    p.name,
                    p.annotation,
                    default_factory=default_factory,
                    parent=root,
                )
                if dataclasses.is_dataclass(p.annotation):
                    # Hierarchical arguments
                    param.children.extend(collect_parameters(p.annotation, param))
                params.append(param)
    root = dataclasses.replace(root, children=params)
    return root


def preprocess_argparse_parameter(param: Parameter, children):
    handled = False
    param = dataclasses.replace(param, children=children)
    if param.name is not None:
        for h in handlers:
            handled, param = h.preprocess_argparse_parameter(param)
            if handled:
                break
    return param


def bind_argparse_arguments(
        parameters: Parameter, argparse_args, ignore=None,
        after_parse: Optional[Callable[[Parameter, Namespace, Dict[str, Any]], Dict[str, Any]]] = None):
    args_dict = argparse_args.__dict__
    if '_aparse_parameters' in args_dict:
        args_dict = {k: v for k, v in args_dict.items()}
        parameters = args_dict.pop('_aparse_parameters')

    if ignore is not None:
        parameters = parameters.walk(lambda x, children:
                                     dataclasses.replace(x, children=children) if x.full_name not in ignore else None)

    def bind(parameter: Parameter, children: List[Parameter]):
        # Handle root
        if parameter.name is None:
            return {p.name: x for p, x in children}

        was_handled = False
        value = argparse_args
        for h in handlers:
            was_handled, value = h.bind(parameter, argparse_args)
            if was_handled:
                break
        if was_handled:
            return parameter, value

        if len(children) > 0:
            if dataclasses.is_dataclass(parameter.type):
                value = parameter.type(**{p.name: x for p, x in children})
            elif parameter.type == dict:
                value = {p.name: x for p, x in children}
            else:
                raise RuntimeError(f'Aggregate type {parameter.type} is not supported')
        else:
            value = args_dict[parameter.argument_name]
            if value == parameter.default:
                value = parameter.default_factory()
            else:
                was_handled = False
                for handler in handlers:
                    was_handled, value = handler.parse_value(parameter, value)
                    if was_handled:
                        break
        return parameter, value
    kwargs = parameters.walk(bind)
    if after_parse is not None:
        kwargs = after_parse(parameters, argparse_args, kwargs)
    return kwargs


def from_argparse_arguments(parameters: Parameter, function, argparse_args, *args, _ignore=None, _prefix: str = None, _after_parse=None, **kwargs):
    new_kwargs = bind_argparse_arguments(parameters, argparse_args, ignore=set(kwargs.keys()).union(_ignore or []), after_parse=_after_parse)
    if _prefix is not None:
        new_kwargs = new_kwargs[_prefix]
    new_kwargs.update(kwargs)
    return function(*args, **new_kwargs)


def _parse_arguments_manually(args, defaults):
    kwargs = dict(**defaults)
    if args is None:
        # args default to the system args
        args = sys.argv[1:]
    else:
        # make sure that args are mutable
        args = list(args)

    for nm, val in zip(args, args[1:]):
        if nm.startswith('--') and '=' not in nm:
            if val.startswith('--'):
                val = True
            kwargs[nm[2:].replace('-', '_')] = val
        elif val.startswith('--'):
            kwargs[val[2:]] = True
    else:
        for nm in args:
            if nm.startswith('--') and '=' in nm:
                nm, val = nm[2:].split('=', 1)
                kwargs[nm[2:].replace('-', '_')] = val
    return kwargs


def _hack_argparse(parser, parameters, defaults, add_argparse_arguments, before_parse=None):
    super_parse_known_args = parser.parse_known_args
    defaults = dict(**defaults) if defaults is not None else dict()

    def hacked_parse_known_args(args=None, namespace=None):
        kwargs = _parse_arguments_manually(args, defaults)
        new_parameters = getattr(parser, '_aparse_parameters', parameters)
        if before_parse is not None:
            new_parameters = before_parse(new_parameters, parser, kwargs)
            if new_parameters is not None:
                new_parameters = new_parameters.walk(preprocess_argparse_parameter)
                add_argparse_arguments(new_parameters, parser=parser)
        result = super_parse_known_args(args, namespace)
        setattr(result[0], '_aparse_parameters', getattr(parser, '_aparse_parameters', None))
        return result

    setattr(parser, 'parse_known_args', hacked_parse_known_args)
    return parser


def set_defaults(parameters: Parameter, defaults: Dict[str, Any]):
    defaults = dict(**defaults)

    def _call(param, children):
        default_factory = param.default_factory
        if param.full_name in defaults:
            default = defaults.pop(param.full_name)
            default_factory = lambda: default

        return dataclasses.replace(
            param,
            children=children,
            default_factory=default_factory)
    return parameters.walk(_call), defaults


def is_type_compatible(annotation, type2):
    if annotation == type2:
        return True
    meta_name = getattr(getattr(annotation, '__origin__', None), '_name', None)
    if meta_name == 'Literal':
        arg_type = type(annotation.__args__[0])
        return arg_type == type2
    if meta_name == 'Union':
        return any(is_type_compatible(x, type2) for x in annotation.__args__)
    return False


def read_parser_defaults(parameters: Parameter, parser, ignore, soft_defaults: bool = False):
    def map(param, children):
        param = dataclasses.replace(param, children=children)
        choices = param.choices
        default_factory = param.default_factory
        if param.name is None or param.full_name in ignore:
            return param

        for existing_action in parser._actions:
            if existing_action.dest == param.argument_name:
                break
        else:
            return param

        if param.default_factory is not None and not existing_action.required and existing_action.default != param.default:
            if not soft_defaults:
                raise Exception(f'There are conflicting values for {param.argument_name}, [{existing_action.default}, {param.default}]')

        if not is_type_compatible(param.type, existing_action.type):
            raise Exception(f'There are conflicting types for argument {param.argument_name}, [{param.type}, {existing_action.type}]')

        if param.default_factory is None and not existing_action.required:
            # Copy default value
            default = existing_action.default
            default_factory = lambda: default

        if existing_action.choices is not None or choices is not None:
            # Update choices in the literal
            if existing_action.choices is None or choices is None:
                choices = (existing_action.choices or []) + (choices or [])
            else:
                choices = sorted(set(existing_action.choices).intersection(set(choices)))

        return dataclasses.replace(param, choices=choices, default_factory=default_factory)
    return parameters.walk(map)


def merge_parameters(*args):
    root = Parameter(name=None, type=dict)
    children = [y for x in args if x is not None for y in x.children] + [x for x in args if x is not None and x.name is not None]
    children = OrderedDict((y.name, dataclasses.replace(y, parent=root)) for y in children)
    return dataclasses.replace(root, children=list(children.values()))


def add_prefix(parameters, prefix):
    root = Parameter(name=None, type=dict)
    old_root = dataclasses.replace(parameters, parent=root, name=prefix, type=dict)
    old_root = dataclasses.replace(old_root, children=[dataclasses.replace(x, parent=old_root) for x in old_root.children])
    return dataclasses.replace(root, children=[old_root])


def add_argparse_arguments(parameters: Parameter, parser: ArgumentParser,
                           defaults: Dict[str, Any] = None, prefix: str = None,
                           ignore: Set[str] = None, soft_defaults: bool = False, _before_parse=None):
    if prefix is not None:
        parameters = add_prefix(parameters, prefix)
    serialized_call = partial(add_argparse_arguments,
                              defaults=defaults, ignore=ignore, soft_defaults=soft_defaults)
    parser = _hack_argparse(parser, parameters, defaults, serialized_call, _before_parse)
    setattr(parser, '_aparse_parameters', merge_parameters(getattr(parser, '_aparse_parameters', None), parameters))

    if defaults is None:
        defaults = dict()
    parameters, left_defaults = set_defaults(parameters, defaults)
    if left_defaults:
        raise ValueError(f'Some default were not found: {list(left_defaults.keys())}')
    parameters = read_parser_defaults(parameters, parser, list(defaults.keys()), soft_defaults=soft_defaults)

    if ignore is None:
        ignore = {}

    for param in parameters.enumerate_parameters():
        if param.name is None or param.full_name in ignore:
            continue

        for existing_action in parser._actions:
            if existing_action.dest == param.argument_name:
                break
        else:
            existing_action = None

        was_handled = False
        for h in handlers:
            was_handled, parser = h.add_argparse_arguments(param, parser, existing_action=existing_action)
            if was_handled:
                break
        if not was_handled:
            raise RuntimeError('There was no handler registered for adding arguments')
    return parser
