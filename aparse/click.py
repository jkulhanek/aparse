import click
from aparse.core import Parameter, Runtime
from aparse._lib import preprocess_parameter as _preprocess_parameter
from aparse._lib import add_parameters as _add_parameters
from aparse.utils import _empty, get_parameters as _get_parameters
# from click import *  # noqa: F403, F401


class ClickRuntime(Runtime):
    def __init__(self, fn):
        self.fn = fn

    def add_parameter(self, argument_name, argument_type, required=True,
                      help='', default=_empty, choices=None):
        if choices is not None:
            argument_type = click.Choice(choices, case_sensitive=True)
        if argument_type is not None:
            self.fn = click.option(f'--{argument_name.replace("_", "-")}', type=argument_type,
                                   required=required, default=default if default != _empty else None,
                                   show_default=default != _empty, help=help,
                                   show_choices=choices is not None)(self.fn)

    def read_defaults(self, parameters: Parameter):
        # This is not needed, click will call parse only once
        return parameters

    def add_parameters(self, parameters: Parameter):
        _add_parameters(parameters, self)


def command(*args, **kwargs):
    _wrap = click.command(*args, **kwargs)

    def wrap(fn):
        root_param = _get_parameters(fn).walk(_preprocess_parameter)
        fn = _wrap(fn)
        runtime = ClickRuntime(fn)
        runtime.add_parameters(root_param)
        return fn

    return wrap
