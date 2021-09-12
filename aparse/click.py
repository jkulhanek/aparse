import click
from aparse.core import Parameter, Runtime, DefaultFactory
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
    def __init__(self, fn, soft_defaults=False):
        self.fn = fn
        self.soft_defaults = soft_defaults
        self._parameters = None
        self._after_parse_callbacks = []

    def add_parameter(self, argument_name, argument_type, required=True,
                      help='', default=_empty, choices=None):
        if choices is not None:
            argument_type = click.Choice(choices, case_sensitive=True)
        if argument_type is not None:
            params = self._get_params()
            existing_action = {x.name: x for x in params}.get(argument_name, None)
            if existing_action is not None:
                params.remove(existing_action)

            opt_argument_name = '/'.join(f'--{x}' for x in argument_name.replace('_', '-').split('/'))
            self.fn = click.option(opt_argument_name, type=argument_type,
                                   required=required, default=default if default != _empty else None,
                                   show_default=default != _empty, help=help,
                                   show_choices=choices is not None)(self.fn)

    def _get_params(self):
        return getattr(self.fn, 'params', getattr(self.fn, '__click_params__', []))

    @staticmethod
    def _get_click_type(click_type):
        if click_type == click.INT:
            return int
        elif click_type == click.STRING:
            return str
        elif click_type == click.FLOAT:
            return float
        elif click_type == click.BOOL:
            return bool
        elif isinstance(click_type, click.Choice):
            return type(click_type.choices[0] if len(click_type.choices) > 0 else None)
        return click_type

    def read_defaults(self, parameters: Parameter):
        params = self._get_params()
        if len(params) == 0:
            return parameters
        param_map = {x.name: x for x in params}

        def map(param, children):
            choices = param.choices
            default_factory = param.default_factory
            if param.name is None or param.type is None or len(param.children) > 0:
                return param.replace(children=children)

            existing_action = param_map.get(param.argument_name, None)
            if existing_action is None:
                return param.replace(children=children)

            default_factory = DefaultFactory.get_factory(existing_action.default)
            if existing_action.required:
                default_factory = None
            if isinstance(existing_action.type, click.Choice):
                choices = existing_action.type.choices
            argument_type = self._get_click_type(existing_action.type)
            return param.replace(choices=choices, default_factory=default_factory,
                                 argument_type=argument_type, children=children)
        return parameters.walk(map)

    def add_parameters(self, parameters: Parameter):
        _add_parameters(parameters, self, soft_defaults=self.soft_defaults)

        if self._parameters is not None:
            parameters = merge_parameter_trees(self._parameters, parameters)
        self._parameters = parameters


def _get_command_class(cls=None):
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


def command(name=None, cls=None, before_parse=None, after_parse=None, soft_defaults=False, **kwargs):
    cls = _get_command_class(cls)
    _wrap = click.command(name=name, cls=cls, **kwargs)

    def wrap(fn):
        root_param = _get_parameters(fn).walk(_preprocess_parameter)
        runtime = ClickRuntime(fn, soft_defaults=soft_defaults)
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


def _get_group_class(cls=None):
    class Group(cls or click.core.Group):
        def command(self, name=None, cls=None, **kwargs):
            if callable(name):
                return self.command()(name)

            _wrap = command(name=name, cls=cls, **kwargs)

            def wrap(fn):
                fn = _wrap(fn)
                self.add_command(fn)
                return fn
            return wrap
    return Group


def group(name=None, cls=None, **attrs):
    return click.group(name=name, cls=_get_group_class(cls), **attrs)
