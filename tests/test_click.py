import sys
from aparse import click


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
