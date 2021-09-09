from functools import reduce
import dataclasses
import copy
from .core import Parameter


_empty = object()


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
