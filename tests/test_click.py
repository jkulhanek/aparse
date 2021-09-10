import sys
from typing import List
from aparse import click
from aparse import ConditionalType, Parameter, AllArguments
from dataclasses import dataclass


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
