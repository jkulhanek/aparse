from argparse import ArgumentParser
import dataclasses
from typing import Type, Any, NewType, Dict, Union, Callable, List, Tuple
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

    @property
    def full_name(self):
        if self.parent is not None and self.parent.name is not None:
            return self.parent.full_name + '.' + self.name
        return self.name

    @property
    def argument_name(self):
        return self.full_name.replace('.', '_')

    def walk(self, fn: Callable[['Parameter', List[Any]], Union['Parameter', Dict, None]]):
        new_children = []
        for p in self.children:
            result = p.walk(fn)
            if result is not None:
                new_children.append(result)
        return fn(self, children=new_children)

    def enumerate_parameters(self):
        yield self
        for x in self.children:
            for y in x.enumerate_parameters():
                yield y

    @property
    def default(self):
        if self.default_factory is None:
            return None
        default = self.default_factory()
        if isinstance(default, (int, str, float, bool)):
            return default
        return _DefaultFactory(self.default_factory)


class Handler:
    def preprocess_argparse_parameter(self, parameter: Parameter) -> Tuple[bool, Type]:
        return False, parameter

    def parse_value(self, parameter: Parameter, value: Any) -> Tuple[bool, Any]:
        return False, value

    def bind(self, parameter: Parameter, args: Dict[str, Any]) -> Tuple[bool, Any]:
        return False, args

    def add_argparse_arguments(self, parameter: Parameter, parser: ArgumentParser, existing_action: Any = None) -> Tuple[bool, ArgumentParser]:
        return False, parser
