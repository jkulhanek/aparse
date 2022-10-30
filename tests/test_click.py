import pytest
import sys
from typing import List
import click as _click
from aparse import click, FunctionConditionalType
from aparse import ConditionalType, Parameter, AllArguments, Literal, WithArgumentName
from dataclasses import dataclass, field


def test_click_all_arguments(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--a', '3', '--b', 'tk'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test(args: AllArguments, b: str, a: int = 5):
        nonlocal was_called
        was_called = True
        assert b == 'tk'
        assert a == 3
        assert isinstance(args, dict)
        assert 'a' in args
        assert 'b' in args

    test()
    assert was_called


def test_click(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--a', '3', '--b', 'tk'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test(b: str, a: int = 5):
        nonlocal was_called
        was_called = True
        assert b == 'tk'
        assert a == 3

    test()
    assert was_called


def test_argparse_parse_arguments_bool_true(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test(k: bool = True):
        nonlocal was_called
        was_called = True
        assert type(k) == bool
        assert k

    test()
    assert was_called


def test_argparse_parse_arguments_bool_false(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--no-k'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test(k: bool = True):
        nonlocal was_called
        was_called = True
        assert type(k) == bool
        assert not k

    test()
    assert was_called


@pytest.mark.parametrize('tp', [int, str, float])
def test_click_types(monkeypatch, tp):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--a', '1'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test(a: tp):
        nonlocal was_called
        was_called = True
        assert a == tp(1)

    test()
    assert was_called


@pytest.mark.parametrize('tp', [bool, int, str, float])
def test_click_read_defaults_types(tp):
    from aparse.click import ClickRuntime
    from aparse.utils import get_parameters

    @_click.option('--k', type=tp, default=tp(1))
    def test(k: tp):
        pass

    runtime = ClickRuntime(test)
    param = runtime.read_defaults(get_parameters(test))
    assert len(param.children) == 1
    assert param.children[0].type == tp
    assert param.children[0].default == tp(1)


def test_click_required(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--a', '3'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test(b: str, a: int = 5):
        nonlocal was_called
        was_called = True
        assert a == 3

    test()
    assert not was_called


def test_parse_arguments_update_no_default(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    @_click.option('--k', type=int, default=1)
    def test(k: int):
        nonlocal was_called
        was_called = True
        assert k == 1

    test()
    assert was_called


def test_parse_arguments_update_different_default_raise_error(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    with pytest.raises(Exception):
        @click.command()
        @_click.option('--k', type=int, default=1)
        def test(k: int = 4):
            nonlocal was_called
            was_called = True

        test()
    assert not was_called


def test_parse_arguments_update_different_soft_default(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command(soft_defaults=True)
    @_click.option('--k', type=int, default=1)
    def test(k: int = 4):
        nonlocal was_called
        was_called = True
        assert k == 4

    test()
    assert was_called


def test_parse_arguments_update_change_required(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command(soft_defaults=True)
    @_click.option('--k', type=int, required=True)
    def test(k: int = 4):
        nonlocal was_called
        was_called = True
        assert k == 4

    assert not test.params[0].required
    test()
    assert was_called


def test_choices(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k', 'a'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test(k: Literal['a', 'b']):
        nonlocal was_called
        was_called = True
        assert k == 'a'

    test()
    assert test.params[0].type.choices == ['a', 'b']
    assert was_called


def test_choices_update(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k', 'a'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    @_click.option('--k', type=_click.Choice(['a', 'c']))
    def test(k: Literal['a', 'b']):
        nonlocal was_called
        was_called = True
        assert k == 'a'

    test()
    assert test.params[0].type.choices == ['a']
    assert was_called


def test_choices_update2(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k', 'a'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    @_click.option('--k', type=str)
    def test(k: Literal['a', 'b']):
        nonlocal was_called
        was_called = True
        assert k == 'a'

    test()
    assert test.params[0].type.choices == ['a', 'b']
    assert was_called


def test_click_dataclasses(monkeypatch):
    @dataclass
    class D1:
        test: str

    monkeypatch.setattr(sys, 'argv', ['prg.py', '--test2', '5', '--data1-test', 'ok'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test_fn(data1: D1, test2: int):
        nonlocal was_called
        was_called = True
        assert test2 == 5
        assert isinstance(data1, D1)
        assert data1.test == 'ok'

    test_fn()
    assert was_called


def test_click_classes(monkeypatch):
    class D1:
        def __init__(self, test: str):
            self.test = test

    monkeypatch.setattr(sys, 'argv', ['prg.py', '--test2', '5', '--data1-test', 'ok'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test_fn(data1: D1, test2: int):
        nonlocal was_called
        was_called = True
        assert test2 == 5
        assert isinstance(data1, D1)
        assert data1.test == 'ok'

    test_fn()
    assert was_called


def test_click_nested_dataclasses_2levels(monkeypatch):
    @dataclass
    class D1:
        test: str

    @dataclass
    class D2:
        data1: D1
        test2: int

    monkeypatch.setattr(sys, 'argv', ['prg.py', '--test2', '5', '--data2-test2', '3', '--data2-data1-test', 'ok'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def test_fn(data2: D2, test2: int):
        nonlocal was_called
        was_called = True
        assert test2 == 5
        assert isinstance(data2, D2)
        assert isinstance(data2.data1, D1)
        assert data2.data1.test == 'ok'
        assert data2.test2 == 3

    test_fn()
    assert was_called


def test_parse_list(monkeypatch):
    was_called = False

    @click.command()
    def test_fn(d: List[int], e: List[str]):
        nonlocal was_called
        was_called = True
        assert len(d) == 2
        assert d[0] == 2
        assert d[1] == 3

        assert len(e) == 2
        assert e[0] == 'te'
        assert e[1] == 'st'

    monkeypatch.setattr(sys, 'argv', ['prg.py', '--d', '2,3', '--e', 'te,st'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)

    test_fn()
    assert was_called


def test_parse_from_str(monkeypatch):
    was_called = False

    class CS:
        def __init__(self, a):
            self.a = a

        @staticmethod
        def from_str(str_val):
            return CS(f'ok-{str_val}')

    @click.command()
    def test_fn(d: CS):
        nonlocal was_called
        was_called = True
        assert isinstance(d, CS)
        assert d.a == 'ok-test'

    monkeypatch.setattr(sys, 'argv', ['prg.py', '--d', 'test'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)

    test_fn()
    assert was_called


def test_click_before_parse_callback(monkeypatch):
    was_called = False
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k', '3'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)

    def callback(param, parser, kwargs):
        assert 'k' in kwargs
        return Parameter(name='test', type=int, default_factory=lambda: 5)

    @click.command(before_parse=callback)
    def testfn(k: int = 1, **kwargs):
        nonlocal was_called
        was_called = True
        assert 'test' in kwargs
        assert kwargs['test'] == 5

    testfn()
    assert was_called


def test_click_after_parse_callback(monkeypatch):
    was_called = False
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k', '3'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)

    def callback(param, argparse_args, kwargs):
        kwargs['k'] += 1
        return kwargs

    @click.command(after_parse=callback)
    def testfn(k: int = 1):
        nonlocal was_called
        was_called = True
        assert k == 4

    testfn()
    assert was_called


def test_click_conditional_matching_prefix(monkeypatch):
    was_called = False
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k', 'd2', '--k-prop-d2', 'ok'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)

    @dataclass
    class D1:
        prop_d2: str = 'test'

    @dataclass
    class D2:
        prop_d2: str = 'test-d2'

    class DSwitch(ConditionalType):
        d1: D1
        d2: D2

    @click.command()
    def testfn(k: DSwitch):
        nonlocal was_called
        was_called = True
        assert isinstance(k, D2)
        assert k.prop_d2 == 'ok'

    testfn()
    assert was_called


def test_click_conditional_matching_no_prefix(monkeypatch):
    was_called = False
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--k', 'd2', '--prop-d2', 'ok'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)

    @dataclass
    class D1:
        prop_d2: str = 'test'

    @dataclass
    class D2:
        prop_d2: str = 'test-d2'

    class DSwitch(ConditionalType, prefix=False):
        d1: D1
        d2: D2

    @click.command()
    def testfn(k: DSwitch):
        nonlocal was_called
        was_called = True
        assert isinstance(k, D2)
        assert k.prop_d2 == 'ok'

    testfn()
    assert was_called


def test_click_groups(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', 'test-a', '--a', '3', '--b', 'tk'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.group()
    def main():
        pass

    @main.command('test-b')
    def testb():
        pass

    @main.command('test-a')
    def test(b: str, a: int = 5):
        nonlocal was_called
        was_called = True
        assert b == 'tk'
        assert a == 3

    main()
    assert was_called


def test_click_groups2(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', 'test-a', '--a', '3', '--b', 'tk'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.group()
    def main():
        pass

    @main.command
    def testb():
        pass

    @main.command('test-a')
    def test(b: str, a: int = 5):
        nonlocal was_called
        was_called = True
        assert b == 'tk'
        assert a == 3

    main()
    assert was_called


def test_click_groups_late_registration(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', 'test-a', '--a', '3', '--b', 'tk'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.group()
    def main():
        pass

    @click.command('test-a')
    def test(b: str, a: int = 5):
        nonlocal was_called
        was_called = True
        assert b == 'tk'
        assert a == 3

    main.add_command(test)
    main()
    assert was_called


def test_click_function_conditional_matching(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py', '--r', '2', '--k-prop-d2', 'ok'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @dataclass
    class D1:
        prop_d2: str = 'test'

    @dataclass
    class D2:
        prop_d2: str = 'test-d2'

    FSwitch = FunctionConditionalType(lambda kwargs: D2 if (kwargs.get('r', None) == '2') else D1)

    @click.command()
    def testfn(k: FSwitch, r: str):
        nonlocal was_called
        was_called = True
        assert isinstance(k, D2)
        assert k.prop_d2 == 'ok'

    testfn()
    assert was_called


def test_click_function_conditional_matching_no_match(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    FSwitch = FunctionConditionalType(lambda kwargs: None)

    @click.command()
    def testfn(k: FSwitch = None):
        nonlocal was_called
        was_called = True
        assert k is None

    testfn()
    assert was_called


def test_special_case_1(monkeypatch):
    @dataclass
    class TestClass:
        pass

    FClass = FunctionConditionalType(lambda *_, **_k: TestClass, False)
    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def testfn(k: FClass):
        nonlocal was_called
        was_called = True
        assert k is not None
        assert isinstance(k, TestClass)

    testfn()
    assert was_called


def test_special_case_2(monkeypatch):
    @dataclass
    class TestClass:
        pass

    FClass = FunctionConditionalType(lambda *_, **_k: TestClass, False)

    @dataclass
    class TestClass2:
        c: FClass

    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def testfn(k: WithArgumentName(TestClass2)):
        nonlocal was_called
        was_called = True
        assert k is not None
        assert k.c is not None
        assert isinstance(k.c, TestClass)

    testfn()
    assert was_called


def test_special_case_3(monkeypatch):
    @dataclass
    class MaskStrategy:
        @classmethod
        def from_str(cls, value):
            if cls == MaskStrategy:
                # Root parser will find try all subclasses
                def all_subclasses(cls):
                    return set(cls.__subclasses__()).union(
                        [s for c in cls.__subclasses__() for s in all_subclasses(c)])
                for sub_cls in all_subclasses(cls):
                    try:
                        return sub_cls.from_str(value)
                    except ValueError:
                        pass
                else:
                    raise ValueError(f'Value {value} could not be parsed by any known parser')

            if value != cls.__name__:
                raise ValueError(f'Value {value} cannot be parsed as {cls.__name__} class')
            return cls()

    @dataclass
    class BertMaskStrategy(MaskStrategy):
        pass

    @dataclass
    class BertSubsequenceMaskStrategy(MaskStrategy):
        mask_ratio: float = 0.15

    @dataclass
    class Config:
        a: MaskStrategy = field(default_factory=BertMaskStrategy)

    monkeypatch.setattr(sys, 'argv', ['prg.py', '--c-a', 'BertSubsequenceMaskStrategy'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def testfn(c: Config):
        nonlocal was_called
        was_called = True
        assert c is not None
        assert c.a is not None
        assert isinstance(c.a, BertSubsequenceMaskStrategy)

    testfn()
    assert was_called


def test_special_case_4(monkeypatch):
    @dataclass
    class MaskStrategy:
        @classmethod
        def from_str(cls, value):
            if cls == MaskStrategy:
                # Root parser will find try all subclasses
                def all_subclasses(cls):
                    return set(cls.__subclasses__()).union(
                        [s for c in cls.__subclasses__() for s in all_subclasses(c)])
                for sub_cls in all_subclasses(cls):
                    try:
                        return sub_cls.from_str(value)
                    except ValueError:
                        pass
                else:
                    raise ValueError(f'Value {value} could not be parsed by any known parser')

            if value != cls.__name__:
                raise ValueError(f'Value {value} cannot be parsed as {cls.__name__} class')
            return cls()

        def __str__(self):
            return repr(self)

        def __repr__(self):
            return self.__class__.__name__

    @dataclass
    class BertMaskStrategy(MaskStrategy):
        pass

    @dataclass
    class BertSubsequenceMaskStrategy(MaskStrategy):
        mask_ratio: float = 0.15

    @dataclass
    class Config:
        a: MaskStrategy = field(default_factory=BertMaskStrategy)

    monkeypatch.setattr(sys, 'argv', ['prg.py'])
    monkeypatch.setattr(sys, 'exit', lambda *args, **kwargs: None)
    was_called = False

    @click.command()
    def testfn(c: Config):
        nonlocal was_called
        was_called = True
        assert c is not None
        assert c.a is not None
        assert isinstance(c.a, BertMaskStrategy)

    testfn()
    assert was_called
