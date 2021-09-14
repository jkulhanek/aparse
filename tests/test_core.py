from aparse.utils import get_parameters
from aparse.core import ConditionalType, ForwardParameters
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


def test_forward_parameters_kwargs():
    def fn(a: int, b: str = 3):
        pass

    fn2 = ForwardParameters(fn, a=4)
    param = get_parameters(fn2)
    assert param.find('a') is None
    assert param.find('b').default == 3


def test_forward_parameters_args():
    def fn(a: int, b: str = 3):
        pass

    fn2 = ForwardParameters(fn, 4)
    param = get_parameters(fn2)
    assert param.find('a') is None
    assert param.find('b').default == 3


def test_forward_parameters_class_kwargs():
    class A:
        def __init__(self, a: int, b: str = 3):
            pass

    B = ForwardParameters(A, a=4)
    param = get_parameters(B)
    assert param.find('a') is None
    assert param.find('b').default == 3


def test_forward_parameters_class_args():
    class A:
        def __init__(self, a: int, b: str = 3):
            pass

    B = ForwardParameters(A, 4)
    param = get_parameters(B)
    assert param.find('a') is None
    assert param.find('b').default == 3
