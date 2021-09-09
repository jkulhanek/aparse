from typing import List
from aparse import add_argparse_arguments, ArgparseArguments, Parameter
from aparse.utils import get_path
from aparse import ConditionalType
from argparse import ArgumentParser
from dataclasses import dataclass


def test_parse_arguments():
    @add_argparse_arguments()
    def testfn(k: int = 1, m: float = 2.):
        return dict(k=k, m=m)

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', '3'])

    assert hasattr(args, 'k')
    assert hasattr(args, 'm')

    d = testfn.from_argparse_arguments(args)
    assert d['k'] == 3
    assert d['m'] == 2.


def test_hacked_argparse_registered():
    @add_argparse_arguments()
    def testfn():
        pass

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args([])

    assert hasattr(args, '_aparse_parameters')


def test_parse_arguments_forward_arguments():
    @add_argparse_arguments()
    def testfn(k: int = 1, m: float = 2.):
        return dict(k=k, m=m)

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', '3'])

    assert hasattr(args, 'k')
    assert hasattr(args, 'm')

    d = testfn.from_argparse_arguments(args, k=4, m=1)
    assert d['k'] == 4
    assert d['m'] == 1


def test_parse_arguments_ignore():
    @add_argparse_arguments(ignore={'m'})
    def testfn(k: int = 1, m: float = 2.):
        return dict(k=k, m=m)

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', '3'])

    assert hasattr(args, 'k')
    assert not hasattr(args, 'm')

    d = testfn.from_argparse_arguments(args)
    assert d['k'] == 3
    assert d['m'] == 2


def test_bind_arguments():
    @add_argparse_arguments()
    def testfn(k: int = 1, m: float = 2.):
        return dict(k=k, m=m)

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', '3'])

    assert hasattr(args, 'k')
    assert hasattr(args, 'm')

    d = testfn.bind_argparse_arguments(args)
    assert isinstance(d, dict)
    assert d['k'] == 3
    assert d['m'] == 2.


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


def test_argparse_arguments_with_prefix():
    @add_argparse_arguments()
    def testfn(args: ArgparseArguments, k: int = 1, m: float = 2.):
        return dict(k=k, m=m)

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser, prefix='test1')
    args = argparser.parse_args(['--test1-k', '3'])

    assert hasattr(args, 'test1_k')
    assert hasattr(args, 'test1_m')

    d = testfn.from_argparse_arguments(args, _prefix='test1')
    assert isinstance(d, dict)
    assert d['k'] == 3
    assert d['m'] == 2.


def test_argparse_arguments_with_prefix2():
    @add_argparse_arguments()
    def testfn(args: ArgparseArguments, k: int = 1, m: float = 2.):
        return dict(k=k, m=m)

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser, prefix='test1')
    argparser = testfn.add_argparse_arguments(argparser, prefix='test2')
    args = argparser.parse_args(['--test1-k', '3', '--test2-k', '4'])

    assert hasattr(args, 'test1_k')
    assert hasattr(args, 'test1_m')
    assert hasattr(args, 'test2_k')
    assert hasattr(args, 'test2_m')

    d = testfn.bind_argparse_arguments(args)
    assert isinstance(d, dict)
    assert 'test1' in d
    assert 'test2' in d

    d = testfn.from_argparse_arguments(args, _prefix='test1')
    assert isinstance(d, dict)
    assert d['k'] == 3
    assert d['m'] == 2.

    d = testfn.from_argparse_arguments(args, _prefix='test2')
    assert isinstance(d, dict)
    assert d['k'] == 4
    assert d['m'] == 2.


def test_aparse_before_parse_callback():
    def callback(param, parser, kwargs):
        assert 'k' in kwargs
        return Parameter(name='test', type=str, default_factory=lambda: 5)

    @add_argparse_arguments(before_parse=callback)
    def testfn(k: int = 1, **kwargs):
        return kwargs

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', '3'])

    assert hasattr(args, 'k')
    assert hasattr(args, 'test')

    d = testfn.from_argparse_arguments(args)
    assert 'test' in d
    assert d['test'] == 5


def test_aparse_after_parse_callback():
    def callback(param, argparse_args, kwargs):
        kwargs['k'] += 1
        return kwargs

    @add_argparse_arguments(after_parse=callback)
    def testfn(k: int = 1):
        return k

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', '3'])

    assert hasattr(args, 'k')

    d = testfn.from_argparse_arguments(args)
    assert d == 4


def test_aparse_conditional_matching():
    @dataclass
    class D1:
        prop_d2: str = 'test'

    @dataclass
    class D2:
        prop_d2: str = 'test-d2'

    class DSwitch(ConditionalType):
        d1: D1
        d2: D2

    @add_argparse_arguments
    def testfn(k: DSwitch):
        return k

    argparser = ArgumentParser()
    argparser = testfn.add_argparse_arguments(argparser)
    args = argparser.parse_args(['--k', 'd2', '--k-prop-d2', 'ok'])
    assert hasattr(args, 'k')

    k = testfn.from_argparse_arguments(args)
    assert isinstance(k, D2)
    assert k.prop_d2 == 'ok'


def test_utils_prefix_parameter():
    from aparse.utils import prefix_parameter

    p = Parameter(name='test', type=str)
    p2 = prefix_parameter(p, 'a.bb.ccc')
    assert get_path(p2, 'bb.ccc.test').name == 'test'
