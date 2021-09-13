import sys
from typing import List, Dict, Any, Tuple
import dataclasses
from .core import Parameter, ParameterWithPath, Handler, Runtime, DefaultFactory
from .utils import merge_parameter_trees, consolidate_parameter_tree
from .utils import ignore_parameters


handlers: List[Handler] = []


def register_handler(handler):
    handlers.insert(0, handler())
    return handler


def preprocess_parameter(param: ParameterWithPath, children):
    handled = False
    param = param.replace(children=children)
    if param.name is not None:
        for h in handlers:
            handled, param = h.preprocess_parameter(param)
            if handled:
                break
    return param


def parse_arguments_manually(args=None, defaults=None):
    kwargs = dict(**defaults) if defaults is not None else dict()
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


def handle_before_parse(runtime: Runtime, parameters: Parameter, kwargs: Dict[str, str], callbacks=None):
    added_params: List[Parameter] = []
    for bp in [getattr(h, 'before_parse', None) for h in reversed(handlers)] + (callbacks or []):
        if bp is None:
            continue
        np = bp(merge_parameter_trees(*([parameters] + added_params)), runtime, kwargs)
        if np is not None:
            added_params.append(np)

    if len(added_params) > 0:
        return merge_parameter_trees(*added_params).walk(preprocess_parameter)
    return None


def handle_after_parse(parameters: Parameter, arguments: Dict[str, Any], kwargs: Dict[str, Any], callbacks=None):
    for ap in [getattr(h, 'after_parse', None) for h in reversed(handlers)] + (callbacks or []):
        if ap is None:
            continue
        kwargs = ap(parameters, arguments, kwargs)
    return kwargs


def set_defaults(parameters: Parameter, defaults: Dict[str, Any]):
    defaults = dict(**defaults)

    def _call(param, children):
        default_factory = param.default_factory
        if param.full_name in defaults:
            default = defaults.pop(param.full_name)
            default_factory = DefaultFactory.get_factory(default)
        return param.replace(
            children=children,
            default_factory=default_factory)
    return parameters.walk(_call), defaults


def add_parameters(parameters: Parameter, runtime: Runtime,
                   defaults: Dict[str, Any] = None,
                   soft_defaults: bool = False):
    if defaults is not None:
        parameters, left_defaults = set_defaults(parameters, defaults)
        if left_defaults:
            raise ValueError(f'Some default were not found: {list(left_defaults.keys())}')

    default_parameters = runtime.read_defaults(parameters)
    if defaults is not None:
        default_parameters = ignore_parameters(default_parameters, set(defaults.keys()))
    parameters = merge_parameter_trees(default_parameters, parameters)
    parameters = consolidate_parameter_tree(parameters, soft_defaults=soft_defaults)
    # TODO: implement default's type validation!
    # parameters = merge_parameter_defaults(parameters, default_parameters, soft_defaults=soft_defaults)

    for param in parameters.enumerate_parameters():
        for h in handlers:
            if h.add_parameter(param, runtime):
                break
        else:
            raise RuntimeError('There was no handler registered for adding arguments')


def bind_parameters(parameters: Parameter, arguments: Dict[str, Any]):
    def bind(parameter: ParameterWithPath, children: List[Tuple[Parameter, Any]]):
        was_handled = False
        value = arguments
        for h in handlers:
            was_handled, value = h.bind(parameter, arguments, children)
            if was_handled:
                break
        if was_handled:
            return parameter, value

        if len(children) > 0 or parameter.name is None:
            if dataclasses.is_dataclass(parameter.type):
                value = parameter.type(**{p.name: x for p, x in children})
            elif parameter.type == dict:
                value = {p.name: x for p, x in children if p.name is not None}
            else:
                value = parameter.type(**{p.name: x for p, x in children})
        else:
            value = arguments[parameter.argument_name]
            if value == parameter.default:
                value = parameter.default_factory()
            else:
                was_handled = False
                for handler in handlers:
                    was_handled, value = handler.parse_value(parameter, value)
                    if was_handled:
                        break
        return parameter, value
    _, kwargs = parameters.walk(bind)
    return kwargs
