import inspect
import sys
import argparse
import dataclasses
from functools import partial
from typing import NewType, Dict, Any
try:
    from typing import Literal
except(ImportError):
    # Literal polyfill
    class _Literal:
        @classmethod
        def __getitem__(cls, key):
            tp = key[0] if isinstance(key, tuple) else key
            return type(tp)
    Literal = _Literal()


ArgparseArguments = NewType('ArgparseArguments', Dict[str, Any])


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


def add_argparse_arguments(ignore=None, before_parse=None, after_parse=None):
    if ignore is None:
        ignore = set()

    def _wrap(obj):
        # if dataclasses.is_dataclass(obj):
        #     raise NotImplementedError()
        parameters = (_preprocess_param(x) for x in _get_parameters(obj, ignore))
        parameters = [x for x in parameters if x is not None]
        setattr(obj, 'add_argparse_arguments', _build_add_argparse_arguments(parameters, before_parse))
        setattr(obj, 'from_argparse_arguments', _build_from_argparse_arguments(obj, parameters, after_parse))
        setattr(obj, 'bind_argparse_arguments', _build_bind_argparse_arguments(parameters))
        return obj
    return _wrap


def get_named_parameters(function):
    params = _get_parameters(function, {})
    return {x[0] for x in params if x[0] != 'self'}


def _get_parameters(obj, ignore):
    def collect_parameters(cls, generated=None, prefix='', parent_type=None):
        if parent_type is None:
            parent_type = tuple()
        if generated is None:
            generated = set()
        output = []
        parameters = inspect.signature(cls.__init__).parameters
        calls_parent = False
        for p in parameters.values():
            if p.kind == inspect.Parameter.VAR_KEYWORD:
                for base in cls.__bases__:
                    calls_parent = True
            if p.kind == inspect.Parameter.KEYWORD_ONLY or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                if p.name not in generated and p.name not in ignore:
                    default = p.default
                    if dataclasses.is_dataclass(cls) and isinstance(default, dataclasses._HAS_DEFAULT_FACTORY_CLASS):
                        default = _DefaultFactory(cls.__dataclass_fields__[p.name].default_factory)
                    if dataclasses.is_dataclass(p.annotation):
                        # Hierarchical arguments
                        output.append((f'{prefix}{p.name}', '', p.annotation, default))
                        output.extend(collect_parameters(p.annotation, generated, prefix=f'{prefix}{p.name}.', parent_type=parent_type + (p.annotation,)))
                    else:
                        output.append((f'{prefix}{p.name}', f'{prefix.replace(".", "_")}{p.name}', p.annotation, default, parent_type + (p.annotation,)))
                        generated.add(p.name)
        if calls_parent:
            output.extend(collect_parameters(base, generated, prefix=prefix))
        return output

    if inspect.isclass(obj):
        params = collect_parameters(obj)
    else:
        params = []
        parameters = inspect.signature(obj).parameters
        for p in parameters.values():
            if p.kind == inspect.Parameter.KEYWORD_ONLY or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                if p.name not in ignore:
                    if dataclasses.is_dataclass(p.annotation):
                        # Hierarchical arguments
                        params.extend(collect_parameters(p.annotation, set(params), prefix=f'{p.name}.', parent_type=(p.annotation,)))
                    else:
                        params.append((p.name, p.name, p.annotation, p.default, tuple()))
    return params


class _DefaultFactory:
    def __init__(self, factory):
        self.factory = factory

    def __repr__(self):
        return repr(self.factory())

    def __str__(self):
        return str(self.factory())

    def __call__(self):
        return self.factory()


def _preprocess_param(param):
    *names, annotation, default, par_type = param
    if annotation is None:
        return None

    choices = None
    meta_name = getattr(getattr(annotation, '__origin__', None), '_name', None)
    arg_type = None
    if annotation == ArgparseArguments:
        arg_type = ArgparseArguments
    if meta_name == 'Literal':
        arg_type = type(annotation.__args__[0])
        choices = annotation.__args__
    elif meta_name == 'Union':
        tp = set((x for x in annotation.__args__ if not isinstance(None, x)))
        if str in tp:
            arg_type = str
        if int in tp:
            arg_type = int
        if float in tp:
            arg_type = float
    elif hasattr(annotation, 'from_str') and callable(annotation.from_str):
        arg_type = str
    elif isinstance(default, bool):
        arg_type = bool
    elif annotation in [int, float, str, bool]:
        arg_type = annotation
    elif getattr(annotation, '__origin__', None) == list:
        tp = annotation.__args__[0]
        if tp in (int, str, float):
            arg_type = str
    if arg_type is not None:
        return tuple(names) + (annotation, arg_type, default, choices, par_type)


def _add_before_parse(parser, before_parse, defaults):
    if before_parse is None:
        return parser

    super_parse_known_args = parser.parse_known_args
    defaults = dict(**defaults)

    def hacked_parse_known_args(args=None, namespace=None):
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

        before_parse(parser, kwargs)
        return super_parse_known_args(args, namespace)

    setattr(parser, 'parse_known_args', hacked_parse_known_args)
    return parser


def _build_add_argparse_arguments(params, before_parse):
    def add_argparse_arguments(parser, defaults=None, ignore=None, soft_defaults=False):
        if defaults is None:
            defaults = dict()
        else:
            defaults = dict(**defaults)
        parser = _add_before_parse(parser, before_parse, defaults)
        if ignore is None:
            ignore = {}
        for long_name, name, annotation, arg_type, default, choices, *_ in params:
            override_default = False
            if name in ignore:
                continue
            if annotation == ArgparseArguments:
                continue
            if name in defaults:
                default = defaults.pop(name)
                override_default = True

            arg_name = name.replace('_', '-')
            help = ''

            # Note, we will check if there already exists an action with the same type
            for existing_action in parser._actions:
                if existing_action.dest == name:
                    break
            else:
                existing_action = None

            if existing_action is not None:
                # We will update default
                if default is not inspect._empty:
                    if existing_action.default is not inspect._empty and not override_default and existing_action.default != default:
                        if not soft_defaults:
                            raise Exception(f'There are conflicting values for {name}, [{existing_action.default}, {default}]')
                        else:
                            default = existing_action.default
                    parser.set_defaults(**{name: default})
                    existing_action.help = f'{help} [{default}]'
                    if existing_action.required:
                        existing_action.required = False
                if not is_type_compatible(annotation, existing_action.type):
                    raise Exception(f'There are conflicting types for argument {name}, [{arg_type}, {existing_action.type}]')
                if choices is not None:
                    # Update choices in the literal
                    existing_action.choices = sorted(set(existing_action.choices or {}).intersection(choices))
            else:
                if arg_type == bool:
                    parser.set_defaults(**{name: default})
                    parser.add_argument(f'--{arg_name}', dest=name, action='store_true', help=f'{help} [{default}]')
                    _arg_name = arg_name
                    if arg_name.startswith('use-'):
                        _arg_name = arg_name[len('use-'):]
                    parser.add_argument(f'--no-{_arg_name}', dest=name, action='store_false', help=f'{help} [{default}]')
                else:
                    if default is not inspect._empty:
                        parser.add_argument(f'--{arg_name}', type=arg_type, choices=choices, default=default, help=f'{help} [{default}]')
                    else:
                        parser.add_argument(f'--{arg_name}', type=arg_type, choices=choices, default=default, required=True, help=f'{help} [required]')

        if defaults:
            raise ValueError(f'Some default were not found: {list(defaults.keys())}')
        return parser

    return add_argparse_arguments


def _from_argparse_arguments(function, parameters, argparse_args, *args, _after_parse=None, **kwargs):
    bind_argparse_arguments = partial(_bind_argparse_arguments, parameters)
    new_kwargs = bind_argparse_arguments(argparse_args, ignore=set(kwargs.keys()))
    new_kwargs.update(kwargs)
    if _after_parse is not None:
        new_kwargs = _after_parse(argparse_args, new_kwargs)
    return function(*args, **new_kwargs)


def _bind_argparse_arguments(parameters, argparse_args, ignore=None):
    def parent_param(x):
        local_name, *rest, par_annot = x
        prefix_len = local_name.index('.') + 1
        local_name = local_name[prefix_len:]
        par_annot = par_annot[1:]
        return (local_name,) + tuple(rest) + (par_annot,)

    kwargs = dict()
    args_dict = argparse_args.__dict__
    skip_params = set()
    for long_name, name, annotation, *_, par_annot in parameters:
        local_name = long_name[:long_name.index('.')] if '.' in long_name else long_name
        if annotation == ArgparseArguments:
            continue
        if name in args_dict and local_name not in skip_params and (ignore is None or local_name not in ignore):
            if par_annot and dataclasses.is_dataclass(par_annot[0]):
                local_parameters = [parent_param(x) for x in parameters if x[0].startswith(f'{local_name}.')]
                kwargs[local_name] = _from_argparse_arguments(par_annot[0], local_parameters, argparse_args)
                skip_params.add(local_name)

            else:
                val = args_dict[name]
                if isinstance(val, str) and hasattr(annotation, 'from_str'):
                    val = annotation.from_str(val)
                if isinstance(val, _DefaultFactory):
                    val = val()
                if getattr(annotation, '__origin__', None) == list and not isinstance(val, list):
                    tp = annotation.__args__[0]
                    if val == '':
                        val = []
                    elif val is not None:
                        val = list(map(tp, val.split(',')))
                kwargs[local_name] = val
    for long_name, name, annotation, *_, par_annot in parameters:
        local_name = long_name[:long_name.index('.')] if '.' in long_name else long_name
        if annotation == ArgparseArguments:
            kwargs[local_name] = args_dict
    return kwargs


def _build_from_argparse_arguments(function, parameters, after_parse=None):
    return partial(_from_argparse_arguments, function, parameters, _after_parse=after_parse)


def _build_bind_argparse_arguments(parameters):
    return partial(_bind_argparse_arguments, parameters)


def add_condition(parser: argparse.ArgumentParser, name, callback, default=None, **kwargs):
    super_parse_known_args = parser.parse_known_args

    def hacked_parse_known_args(args=None, namespace=None):
        if args is None:
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)

        true_val = default
        for nm, val in zip(args, args[1:]):
            if nm == name:
                true_val = val
                break
        else:
            for nm in args:
                if nm.startswith(f'{name}='):
                    true_val = nm[len(f'{name}='):]

        callback(parser, true_val)
        return super_parse_known_args(args, namespace)

    parser.add_argument(name, default=default, **kwargs)
    setattr(parser, 'parse_known_args', hacked_parse_known_args)
