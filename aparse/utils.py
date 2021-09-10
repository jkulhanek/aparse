import inspect
from typing import Any, Callable, Optional, List
from functools import reduce
import dataclasses
import copy
from .core import Parameter, ParameterWithPath, _empty


def get_path(obj, path, default=_empty, _current_path=None):
    if obj == _empty:
        raise IndexError(f'Could not find path {_current_path}.')
    if path == '':
        return obj
    curr, *rest = path.split('.')
    _current_path = curr if _current_path is None else f'{_current_path}.{curr}'
    if hasattr(obj, '__getitem__'):
        if curr in obj:
            obj = obj[curr]
        elif default != _empty:
            return default
        else:
            raise IndexError(f'Could not find path {_current_path}.')
    else:
        if hasattr(obj, curr):
            obj = getattr(obj, curr)
        elif default != _empty:
            return default
        else:
            raise IndexError(f'Could not find path {_current_path}.')

    return get_path(obj, '.'.join(rest), default=default, _current_path=_current_path)


def prefix_parameter(parameter, prefix, container_type=None):
    parameter = copy.copy(parameter)
    has_container = True
    if parameter.name is not None:
        root = Parameter(name=None, type=dict, children=[parameter])
        parameter = root
        has_container = False

    def prefix_single(x, name):
        parent = Parameter(name=name, type=container_type)
        parent.children = x.children
        x.children = [parent]
        return x

    parts = reversed([x for x in prefix.split('.') if x != ''])
    parameter = reduce(prefix_single, parts, parameter)
    if not has_container:
        parameter = parameter.children[0]
    return parameter


def merge_parameter_trees(*args, force=True):
    # Fix single parameters
    def _fix_single_parameter(x):
        if x.name is not None:
            root = Parameter(name=None, type=dict)
            root.children = [x]
            return root
        return x

    parameters = list(map(_fix_single_parameter, (x for x in args if x is not None)))

    def merge_node(a, b):
        if b.type is not None and not force:
            assert a.type == b.type, 'Could not merge structures with different types'
        elif b.type is not None:
            a = a.replace(type=b.type)
        children = list(a.children)
        a = dataclasses.replace(a, children=children)
        # c_map = {a.name: i for i, a in enumerate(children)}
        for c2 in b.children:
            # if c2.name in c_map:
            #     children[c_map[c2.name]] = merge_node(children[c_map[c2.name]], c2)
            # else:
            children.append(dataclasses.replace(c2))
        return a

    return reduce(merge_node, parameters, Parameter(None, dict))


def get_parameters(obj: Any) -> Parameter:
    generated = set()
    root = Parameter(name=None, type=dict)

    def collect_parameters(cls, parent, parent_name=None):
        parameters = inspect.signature(cls.__init__).parameters
        calls_parent = False
        for p in parameters.values():
            if p.name == 'self':
                continue
            if p.kind == inspect.Parameter.VAR_KEYWORD:
                for base in cls.__bases__:
                    calls_parent = True
            if p.kind == inspect.Parameter.KEYWORD_ONLY or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                full_name = f'{parent_name}.{p.name}' if parent_name is not None else p.name
                assert full_name not in generated, f'{full_name} was already generated'
                default_factory = None
                if p.default != p.empty:
                    default_factory = lambda: p.default
                elif dataclasses.is_dataclass(cls) and isinstance(p.default, dataclasses._HAS_DEFAULT_FACTORY_CLASS):
                    default_factory = cls.__dataclass_fields__[p.name].default_factory
                param = Parameter(p.name, p.annotation, default_factory=default_factory)
                generated.add(full_name)
                if dataclasses.is_dataclass(p.annotation):
                    param.children.extend(collect_parameters(p.annotation, param, full_name))
                yield param
        if calls_parent:
            for p in collect_parameters(base, parent, parent_name):
                yield p

    if inspect.isclass(obj):
        params = list(collect_parameters(obj, root, None))
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
                )
                if dataclasses.is_dataclass(p.annotation):
                    # Hierarchical arguments
                    param.children.extend(collect_parameters(p.annotation, param, param.name))
                params.append(param)
    root = root.replace(children=params)
    return root


def walk_multiple(callback: Callable[[List[ParameterWithPath], List[ParameterWithPath]], Optional[ParameterWithPath]],
                  parameter: Parameter, *others: Parameter) -> Parameter:
    def _walk(params):
        children = []
        for p in params[0].children:
            matching_children = [x.find(p.name) for x in params[1:]]
            matching_children = [ParameterWithPath(x, par) for x, par in zip(matching_children, params) if x is not None]
            child = _walk([ParameterWithPath(p, params[0])] + matching_children)
            if child is not None:
                if isinstance(child, ParameterWithPath):
                    child = child.parameter
                children.append(child)

        return callback(params, children)
    return _walk([ParameterWithPath(x, p) for x, p in zip([parameter] + list(others), [None] * (1 + len(others)))]).parameter


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


def merge_parameter_defaults(parameters: Parameter, parameter_defaults: Parameter, soft_defaults: bool = False) -> Parameter:
    def _merge(nodes, children):
        param = nodes[0]
        if param.type is not None and param.name is not None:
            for other in nodes[1:]:
                if other.argument_type == param.argument_type:
                    # Default argument type
                    continue
                default_factory = param.default_factory
                choices = param.choices
                if param.default_factory is not None and other.default_factory is not None and other.default != param.default:
                    if not soft_defaults:
                        raise Exception(f'There are conflicting values for {param.argument_name}, [{other.default}, {param.default}]')

                if not is_type_compatible(param.type, other.argument_type):
                    raise Exception(f'There are conflicting types for argument {param.argument_name}, [{param.type}, {other.argument_type}]')

                if param.default_factory is None and other.default_factory is not None:
                    # Copy default value
                    default = other.default
                    default_factory = lambda: default

                if other.choices is not None or choices is not None:
                    # Update choices in the literal
                    if other.choices is None or choices is None:
                        choices = (other.choices or []) + (choices or [])
                    else:
                        choices = sorted(set(other.choices).intersection(set(choices)))
                param = param.replace(default_factory=default_factory, choices=choices)

        return param.replace(children=children)
    return walk_multiple(_merge, parameters, parameter_defaults)


def ignore_parameters(parameters, ignore):
    def _call(x, children):
        if x.full_name in ignore:
            return None
        return x.replace(children=children)
    return parameters.walk(_call)
