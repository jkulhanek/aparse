import click
from aparse.core import Parameter, Runtime
from aparse._lib import preprocess_parameter as _preprocess_parameter
from aparse._lib import add_parameters as _add_parameters
from aparse._lib import handle_before_parse as _handle_before_parse
from aparse._lib import parse_arguments_manually as _parse_arguments_manually
from aparse._lib import bind_parameters as _bind_parameters
from aparse._lib import handle_after_parse as _handle_after_parse
from aparse.utils import _empty, get_parameters as _get_parameters
from aparse.utils import merge_parameter_trees
# from click import *  # noqa: F403, F401


class ClickRuntime(Runtime):
    def __init__(self, fn):
        self.fn = fn
        self._parameters = None
        self._after_parse_callbacks = []

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

        if self._parameters is not None:
            parameters = merge_parameter_trees(self._parameters, parameters)
        self._parameters = parameters


def get_command_class(cls=None):
    class AparseClickCommand(cls or click.core.Command):
        runtime = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def invoke(self, ctx):
            kwargs = ctx.params
            kwargs = _bind_parameters(self.runtime._parameters, kwargs)
            kwargs = _handle_after_parse(self.runtime._parameters, ctx.params, kwargs, self.runtime._after_parse_callbacks)
            ctx.params = kwargs
            return super().invoke(ctx)
    return AparseClickCommand


def command(name=None, cls=None, before_parse=None, after_parse=None, **kwargs):
    cls = get_command_class(cls)
    _wrap = click.command(name=name, cls=cls, **kwargs)

    def wrap(fn):
        root_param = _get_parameters(fn).walk(_preprocess_parameter)
        runtime = ClickRuntime(fn)
        cls.runtime = runtime
        if after_parse is not None:
            runtime._after_parse_callbacks.append(after_parse)
        runtime.add_parameters(root_param)
        kwargs = _parse_arguments_manually()
        new_param = _handle_before_parse(runtime, root_param, kwargs, [before_parse])
        if new_param is not None:
            runtime.add_parameters(new_param)

        fn = runtime.fn
        fn = _wrap(fn)
        return fn

    return wrap
