from typing import Dict, Set, Any, Optional, Callable
from functools import partial
from argparse import ArgumentParser, Namespace, Action
from .core import Parameter, DefaultFactory, Runtime
from ._lib import add_parameters as _add_parameters
from ._lib import preprocess_parameter as _preprocess_parameter
from ._lib import handle_before_parse as _handle_before_parse
from ._lib import parse_arguments_manually as _parse_arguments_manually
from ._lib import bind_parameters as _bind_parameters
from .utils import _empty, merge_parameter_trees, prefix_parameter
from .utils import ignore_parameters, get_parameters as _get_parameters
from .utils import get_path as _get_path


class ActionNoYes(Action):
    def __init__(self, opt_names, dest, default=True, required=False, help=None):
        self._option_names = opt_names
        super(ActionNoYes, self).__init__(opt_names, dest, nargs=0, const=None, default=default, required=required, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        if option_string == self._option_names[-1]:
            setattr(namespace, self.dest, False)
        else:
            setattr(namespace, self.dest, True)


class ArgparseRuntime(Runtime):
    def __init__(self, parser, soft_defaults: bool = False, defaults=None):
        self.parser = parser
        self._before_parse_callbacks = []
        if hasattr(parser, '_aparse_runtime'):
            old_soft_defaults, old_defaults, self._before_parse_callbacks = parser._aparse_runtime
            assert old_soft_defaults == soft_defaults
            if defaults is not None:
                old_defaults.update(defaults)
            defaults = old_defaults
        else:
            self.parser = self._hack_argparse(self.parser)
        self.soft_defaults = soft_defaults
        self.defaults = defaults or dict()
        self._save()

    def _save(self):
        setattr(self.parser, '_aparse_runtime', (self.soft_defaults, self.defaults, self._before_parse_callbacks))

    def register_before_parse_callback(self, callback):
        self._before_parse_callbacks.append(callback)

    def _hack_argparse(self, parser):
        super_parse_known_args = parser.parse_known_args

        def hacked_parse_known_args(args=None, namespace=None):
            defaults = dict(**self.defaults) if self.defaults is not None else dict()
            kwargs = _parse_arguments_manually(args, defaults)
            old_params = getattr(parser, '_aparse_parameters')
            callbacks = list(self._before_parse_callbacks)
            new_parameters = _handle_before_parse(self, old_params, kwargs, callbacks)
            if new_parameters is not None:
                self.add_parameters(new_parameters)
            setattr(parser, '_aparse_parameters', merge_parameter_trees(old_params, new_parameters))
            result = super_parse_known_args(args, namespace)
            setattr(result[0], '_aparse_parameters', getattr(parser, '_aparse_parameters', None))
            return result

        setattr(parser, 'parse_known_args', hacked_parse_known_args)
        return parser

    def add_parameter(self, argument_name, argument_type, required=True,
                      help='', default=_empty, choices=None):

        full_argument_name = argument_name
        argument_name = argument_name.split('/', 1)[0]
        existing_action = None
        for action in self.parser._actions:
            if action.dest == argument_name:
                existing_action = action
                break

        params = []
        if default != _empty:
            params.append('default: {default}')
        if required:
            params.append('required')
        help = f'{help} [{", ".join(params)}]' if len(params) > 0 else help

        # Find existing action
        if existing_action is not None:
            # We will update default
            existing_action.required = required
            existing_action.help = help
            existing_action.choices = choices
            self.parser.set_defaults(**{argument_name: default if default != _empty else None})
        else:
            arg_type = argument_type
            arg_name = full_argument_name.replace('_', '-')
            if arg_type == bool:
                assert '/' in arg_name
                true_arg_name, false_arg_name = arg_name.split('/', 2)
                self.parser._add_action(ActionNoYes(
                    ['--' + true_arg_name, '--' + false_arg_name], argument_name,
                    default=default if default != _empty else None, required=required, help=help))
            else:
                self.parser.add_argument(f'--{arg_name}', type=arg_type, choices=choices, default=default if default != _empty else None,
                                         required=required,
                                         help=help)

    def read_defaults(self, parameters: Parameter) -> Parameter:
        def map(param, children):
            choices = param.choices
            default_factory = param.default_factory
            if param.name is None or param.type is None or len(param.children) > 0:
                return param.replace(children=children)

            for existing_action in self.parser._actions:
                if existing_action.dest == param.argument_name:
                    break
            else:
                return param.replace(children=children)

            default = existing_action.default
            default_factory = DefaultFactory.get_factory(default)
            if existing_action.required:
                default_factory = None
            argument_type = existing_action.type
            choices = existing_action.choices
            return param.replace(choices=choices, default_factory=default_factory,
                                 argument_type=argument_type, children=children)
        return parameters.walk(map)

    def add_parameters(self, parameters: Parameter):
        # Store parameters
        setattr(self.parser, '_aparse_parameters', merge_parameter_trees(getattr(self.parser, '_aparse_parameters', None), parameters))

        # Add parameters
        _add_parameters(parameters, runtime=self, soft_defaults=self.soft_defaults, defaults=self.defaults)


def _add_argparse_arguments(parameters: Parameter, parser: ArgumentParser,
                            defaults: Dict[str, Any] = None, prefix: str = None,
                            ignore: Optional[Set[str]] = None, soft_defaults: bool = False, _before_parse=None):
    runtime = ArgparseRuntime(parser, soft_defaults=soft_defaults, defaults=defaults)
    if prefix is not None:
        parameters = prefix_parameter(parameters, prefix, dict)
    if ignore is not None:
        parameters = ignore_parameters(parameters, ignore)
    if _before_parse is not None:
        runtime.register_before_parse_callback(_before_parse)
    runtime.add_parameters(parameters)
    return runtime.parser


def _bind_argparse_arguments(
        parameters: Parameter, argparse_args, ignore=None,
        after_parse: Optional[Callable[[Parameter, Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = None):
    args_dict = argparse_args.__dict__
    if '_aparse_parameters' in args_dict:
        args_dict = {k: v for k, v in args_dict.items()}
        parameters = args_dict.pop('_aparse_parameters')

    if ignore is not None:
        parameters = parameters.walk(lambda x, children:
                                     x.replace(children=children) if x.full_name not in ignore else None)

    kwargs, _ = _bind_parameters(parameters, args_dict)
    if after_parse is not None:
        kwargs = after_parse(parameters, args_dict, kwargs)
    return kwargs


def _from_argparse_arguments(parameters: Parameter, function, argparse_args, *args, _ignore=None, _prefix: str = None, _after_parse=None, **kwargs):
    new_kwargs = _bind_argparse_arguments(parameters, argparse_args, ignore=set(kwargs.keys()).union(_ignore or []), after_parse=_after_parse)
    if _prefix is not None:
        new_kwargs = _get_path(new_kwargs, _prefix)
    new_kwargs.update(kwargs)
    return function(*args, **new_kwargs)


def add_argparse_arguments(
        _fn=None, *,
        ignore: Set[str] = None,
        before_parse: Callable[[ArgumentParser, Dict[str, Any]], ArgumentParser] = None,
        after_parse: Callable[[Namespace, Dict[str, Any]], Dict[str, Any]] = None):
    '''
    Extends function or class with "add_argparse_arguments", "from_argparse_arguments", and "bind_argparse_arguments" methods.
    "add_argparse_arguments" adds arguments to the argparse.ArgumentParser instance.
    "from_argparse_arguments" takes the argparse.Namespace instance obtained by calling parse.parse_args(), parses them and calls
        original function or constructs the class
    "bind_argparse_arguments" just parses the arguments into a kwargs dictionary, but does not call the original function. Instead,
        the parameters are returned.

    Arguments:
        ignore: Set of parameters to ignore when inspecting the function signature
        before_parse: Callback to be called before parser.parse_args()
        after_parse: Callback to be called before "from_argparse_arguments" calls the function and updates the kwargs.

    Returns: The original function extended with other functions.
    '''
    def wrap(fn):
        parameters = _get_parameters(fn).walk(_preprocess_parameter)
        if ignore is not None:
            parameters = ignore_parameters(parameters, ignore)
        setattr(fn, 'add_argparse_arguments', partial(_add_argparse_arguments, parameters, _before_parse=before_parse))
        setattr(fn, 'from_argparse_arguments', partial(_from_argparse_arguments, parameters, fn, _after_parse=after_parse))
        setattr(fn, 'bind_argparse_arguments', partial(_bind_argparse_arguments, parameters, after_parse=after_parse))
        return fn

    if _fn is not None:
        return wrap(_fn)
    return wrap
