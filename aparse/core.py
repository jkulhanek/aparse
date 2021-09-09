import sys
from argparse import ArgumentParser
import dataclasses
from typing import Type, Any, NewType, Dict, Union, Callable, List, Tuple, _type_check
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


class _DefaultFactory:
    def __init__(self, factory):
        self.factory = factory

    def __repr__(self):
        return repr(self.factory())

    def __str__(self):
        return str(self.factory())

    def __call__(self):
        return self.factory()


@dataclasses.dataclass
class Parameter:
    name: str
    type: Any
    help: str = ''
    children: List['Parameter'] = dataclasses.field(default_factory=list)
    default_factory: Callable[[], Any] = None
    parent: 'Parameter' = dataclasses.field(default=None, repr=False)
    choices: List[Any] = None
    argument_type: Any = None

    def walk(self, fn: Callable[['Parameter', List[Any]], Union['Parameter', Dict, None]]):
        def _walk(e, parent):
            e = ParameterWithPath(e, parent)
            new_children = []
            for p in e.children:
                result = _walk(p, e)
                if result is not None:
                    if isinstance(result, ParameterWithPath):
                        result = result.parameter
                    new_children.append(result)
            return fn(e, children=new_children)
        result = _walk(self, None)
        if isinstance(result, ParameterWithPath):
            return result.parameter
        return result

    def enumerate_parameters(self):
        def _enumerate(e, parent):
            e = ParameterWithPath(e, parent)
            yield e
            for x in e.children:
                for y in _enumerate(x, e):
                    yield y
        return _enumerate(self, None)

    def __getitem__(self, name):
        for x in self.children:
            if x.name == name:
                return x
        raise IndexError(f'Element {name} not found')

    def __contains__(self, name):
        for x in self.children:
            if x.name == name:
                return True
        return False

    @property
    def default(self):
        if self.default_factory is None:
            return None
        default = self.default_factory()
        if isinstance(default, (int, str, float, bool)):
            return default
        return _DefaultFactory(self.default_factory)

    def __str__(self):
        result = f'{self.name} [{self.type}]\n'
        for x in self.children:
            result += '  ' + str(x).replace('\n', '\n  ')
        return result.strip('\n ')

    def replace(self, **kwargs):
        return dataclasses.replace(self, **kwargs)


@dataclasses.dataclass
class ParameterWithPath:
    parameter: Parameter
    parent: 'ParameterWithPath' = None

    @property
    def name(self):
        return self.parameter.name

    @property
    def type(self):
        return self.parameter.type

    @property
    def argument_type(self):
        return self.parameter.argument_type

    @property
    def children(self):
        return self.parameter.children

    @property
    def default_factory(self):
        return self.parameter.default_factory

    @property
    def default(self):
        return self.parameter.default

    @property
    def choices(self):
        return self.parameter.choices

    @property
    def full_name(self):
        if self.parent is not None and self.parent.name is not None:
            return self.parent.full_name + '.' + self.name
        return self.name

    @property
    def argument_name(self):
        if self.full_name is None:
            return None
        return self.full_name.replace('.', '_')

    def replace(self, **kwargs):
        return ParameterWithPath(self.parameter.replace(**kwargs), self.parent)


class Handler:
    def preprocess_argparse_parameter(self, parameter: ParameterWithPath) -> Tuple[bool, Union[Parameter, ParameterWithPath]]:
        return False, parameter

    def parse_value(self, parameter: ParameterWithPath, value: Any) -> Tuple[bool, Any]:
        return False, value

    def bind(self, parameter: ParameterWithPath, args: Dict[str, Any], children: List[Tuple[Parameter, Any]]) -> Tuple[bool, Any]:
        return False, args

    def add_argparse_arguments(self, parameter: ParameterWithPath, parser: ArgumentParser, existing_action: Any = None) -> Tuple[bool, ArgumentParser]:
        return False, parser


class _ConditionalTypeMeta(type):
    def __new__(cls, name, bases, ns):
        """Create new typed dict class object.
        This method is called when ConditionalType is subclassed,
        or when ConditionalType is instantiated. This way
        ConditionalType supports all three syntax forms described in its docstring.
        Subclasses and instances of ConditionalType return actual dictionaries.
        """
        for base in bases:
            if type(base) is not _ConditionalTypeMeta:
                raise TypeError('cannot inherit from both a ConditionalType type '
                                'and a non-ConditionalType base class')

        annotations = {}
        own_annotations = ns.get('__annotations__', {})
        for base in bases:
            annotations.update(base.__dict__.get('__annotations__', {}))

        annotations.update(own_annotations)
        tp = Union.__getitem__(tuple(annotations.values()))
        setattr(tp, '__conditional_map__', annotations)
        return tp

    __call__ = lambda x: x  # static method

    def __subclasscheck__(cls, other):
        # Typed dicts are only for static structural subtyping.
        raise TypeError('ConditionalType does not support instance and class checks')

    __instancecheck__ = __subclasscheck__


def ConditionalType(typename, fields=None, **kwargs):
    """ConditionalType allows aparse to condition its choices for a
    specific parameter based on an argument.
    Usage::
        class Model(ConditionalType):
            gpt2: GPT2
            resnet: ResNet
    The type info can be accessed via the Model.__annotations__ dict,
    and the Model.__required_keys__ and Model.__optional_keys__ frozensets.
    ConditionalType supports two additional equivalent forms:
        Model = ConditionalType('Model', gpt2=GPT2, resnet=ResNet)
        Model = ConditionalType('Model', dict(gpt2=GPT2, resnet=ResNet))
    The class syntax is only supported in Python 3.6+, while two other
    syntax forms work for Python 2.7 and 3.2+
    """
    if fields is None:
        fields = kwargs
    elif kwargs:
        raise TypeError("ConditionalType takes either a dict or keyword arguments,"
                        " but not both")

    ns = {'__annotations__': dict(fields)}
    try:
        # Setting correct module is necessary to make typed dict classes pickleable.
        ns['__module__'] = sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return _ConditionalTypeMeta(typename, (), ns)


_ConditionalType = type.__new__(_ConditionalTypeMeta, 'ConditionalType', (), {})
ConditionalType.__mro_entries__ = lambda bases: (_ConditionalType,)
