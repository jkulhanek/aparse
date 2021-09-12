import inspect
from typing import Any
from functools import reduce
import dataclasses
import copy
from .core import Parameter, _empty, DefaultFactory


def get_path(obj, path, default=_empty, _current_path=None):
    if obj == _empty:
        raise IndexError(f'Could not find path {_current_path}.')
    if path == '':
        return obj
    curr, *rest = path.split('.')
    _current_path = curr if _current_path is None else f'{_current_path}.{curr}'
    was_found = False
    if isinstance(obj, Parameter):
        obj = obj.find(curr)
        was_found = obj is not None
    else:
        if hasattr(obj, '__getitem__'):
            if curr in obj:
                obj = obj[curr]
                was_found = True
        if not was_found and hasattr(obj, curr):
            obj = getattr(obj, curr)
            was_found = True

    if not was_found:
        if default != _empty:
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


def merge_parameter_trees(*args):
    # Fix single parameters
    def _fix_single_parameter(x):
        if x.name is not None:
            root = Parameter(name=None, type=dict)
            root.children = [x]
            return root
        return x

    parameters = list(map(_fix_single_parameter, (x for x in args if x is not None)))
    return parameters[0].replace(children=[y for x in parameters for y in x.children])


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
                if dataclasses.is_dataclass(cls) and isinstance(p.default, dataclasses._HAS_DEFAULT_FACTORY_CLASS):
                    default_factory = DefaultFactory(cls.__dataclass_fields__[p.name].default_factory)
                else:
                    default_factory = DefaultFactory.get_factory(p.default)

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
                default_factory = DefaultFactory.get_factory(p.default)
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


# def walk_multiple(callback: Callable[[List[ParameterWithPath], List[ParameterWithPath]], Optional[ParameterWithPath]],
#                   parameter: Parameter, *others: Parameter) -> Parameter:
#     def _walk(params):
#         children = []
#         for p in params[0].children:
#             matching_children = [x.find(p.name) for x in params[1:]]
#             matching_children = [ParameterWithPath(x, par) for x, par in zip(matching_children, params) if x is not None]
#             child = _walk([ParameterWithPath(p, params[0])] + matching_children)
#             if child is not None:
#                 if isinstance(child, ParameterWithPath):
#                     child = child.parameter
#                 children.append(child)
# 
#         return callback(params, children)
#     return _walk([ParameterWithPath(x, p) for x, p in zip([parameter] + list(others), [None] * (1 + len(others)))]).parameter


# def is_type_compatible(annotation, type2):
#     if annotation == type2:
#         return True
#     meta_name = getattr(getattr(annotation, '__origin__', None), '_name', None)
#     if meta_name == 'Literal':
#         arg_type = type(annotation.__args__[0])
#         return arg_type == type2
#     if meta_name == 'Union':
#         return any(is_type_compatible(x, type2) for x in annotation.__args__)
#     return False


def consolidate_parameter_tree(parameters: Parameter, soft_defaults: bool = False) -> Parameter:
    def _merge(param, other):
        default_factory = param.default_factory
        choices = param.choices
        if param.type != other.type:
            raise Exception(f'Could not merge parameter {param.full_name} with different types: {param.type}, {other.type}')

        if param.default_factory is not None and other.default_factory is not None and other.default_factory != param.default_factory:
            if not soft_defaults:
                raise Exception(f'There are conflicting values for {param.argument_name}, [{other.default}, {param.default}]')
            else:
                default_factory = other.default_factory

        if param.default_factory is None and other.default_factory is not None:
            # Copy default value
            default_factory = other.default_factory

        if other.choices is not None or choices is not None:
            # Update choices in the literal
            if other.choices is None or choices is None:
                choices = list(other.choices or []) + list(choices or [])
            else:
                choices = sorted(set(other.choices).intersection(set(choices)))
        return param.replace(default_factory=default_factory, choices=choices)

    def _walk(param, children):
        new_children = []
        children_map = dict()
        for c in children:
            if c.name not in children_map:
                children_map[c.name] = len(new_children)
                new_children.append(c)
                continue

            first_c_i = children_map[c.name]
            new_children[first_c_i] = _merge(new_children[first_c_i], c)

        return param.replace(children=new_children)
    return parameters.walk(_walk)


def ignore_parameters(parameters, ignore):
    def _call(x, children):
        if x.full_name in ignore:
            return None
        return x.replace(children=children)
    return parameters.walk(_call)
