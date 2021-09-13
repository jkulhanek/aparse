from aparse.core import ConditionalType
from dataclasses import dataclass


@dataclass
class D1:
    a: str


@dataclass
class D2:
    b: str


def test_conditional_type_subclass():
    class A(ConditionalType):
        a: D1
        b: D2

    assert hasattr(A, '__conditional_map__')


def test_conditional_type_dict():
    A = ConditionalType('A', dict(
        a=D1,
        b=D2
    ))
    assert hasattr(A, '__conditional_map__')


def test_conditional_type_dict2():
    A = ConditionalType('A', dict(
        a=D1,
    ))
    assert hasattr(A, '__conditional_map__')
