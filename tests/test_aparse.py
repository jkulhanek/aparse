from typing import List
from aparse import add_argparse_arguments, ArgparseArguments
import argparse
from argparse import ArgumentParser
from dataclasses import dataclass


def test_argparse_arguments():
    @add_argparse_arguments()
    def testfn(args: ArgparseArguments, k: int = 1, m: float = 2.):
        return args

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', '3'])

    assert hasattr(args, 'k')
    assert hasattr(args, 'm')

    d = testfn.from_argparse_arguments(args)
    assert isinstance(d, dict)
    assert d['k'] == 3
    assert d['m'] == 2.


def test_nested_dataclasses_classes():
    @dataclass
    class D1:
        test: str

    @add_argparse_arguments()
    @dataclass
    class D2:
        data1: D1
        test2: int

    argparser = ArgumentParser()
    D2.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--test2', '5', '--data1-test', 'ok'])

    assert hasattr(args, 'data1_test')
    assert hasattr(args, 'test2')

    d2 = D2.from_argparse_arguments(args)

    assert d2.test2 == 5
    assert isinstance(d2.data1, D1)
    assert d2.data1.test == 'ok'


def test_nested_dataclasses_function_call():
    @dataclass
    class D1:
        test: str

    @add_argparse_arguments()
    def test_fn(data1: D1, test2: int):
        return (data1, test2)

    argparser = ArgumentParser()
    test_fn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--test2', '5', '--data1-test', 'ok'])

    assert hasattr(args, 'data1_test')
    assert hasattr(args, 'test2')

    (data1, test2) = test_fn.from_argparse_arguments(args)

    assert test2 == 5
    assert isinstance(data1, D1)
    assert data1.test == 'ok'


def test_nested_dataclasses_2levels_function_call():
    @dataclass
    class D1:
        test: str

    @add_argparse_arguments()
    @dataclass
    class D2:
        data1: D1
        test2: int

    @add_argparse_arguments()
    def test_fn(data2: D2, test2: int):
        return (data2, test2)

    argparser = ArgumentParser()
    test_fn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--test2', '5', '--data2-test2', '3', '--data2-data1-test', 'ok'])

    assert hasattr(args, 'data2_test2')
    assert hasattr(args, 'data2_data1_test')
    assert hasattr(args, 'test2')

    (data2, test2) = test_fn.from_argparse_arguments(args)

    assert test2 == 5
    assert isinstance(data2, D2)
    assert isinstance(data2.data1, D1)
    assert data2.data1.test == 'ok'
    assert data2.test2 == 3


def test_parse_list():
    @add_argparse_arguments()
    def test_fn(d: List[int], e: List[str]):
        return d, e

    argparser = ArgumentParser()
    test_fn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--d', '2,3', '--e', 'te,st'])

    assert hasattr(args, 'd')
    d, e = test_fn.from_argparse_arguments(args)

    assert len(d) == 2
    assert d[0] == 2
    assert d[1] == 3

    assert len(e) == 2
    assert e[0] == 'te'
    assert e[1] == 'st'


def test_parse_from_str():
    class CS:
        def __init__(self, a):
            self.a = a

        @staticmethod
        def from_str(str_val):
            return CS(f'ok-{str_val}')

    @add_argparse_arguments()
    def test_fn(d: CS):
        return d

    argparser = ArgumentParser()
    test_fn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--d', 'test'])

    assert hasattr(args, 'd')
    d = test_fn.from_argparse_arguments(args)

    assert isinstance(d, CS)
    assert d.a == 'ok-test'
