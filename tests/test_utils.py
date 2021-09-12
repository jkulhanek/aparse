from dataclasses import dataclass, field
import pytest
from collections import namedtuple
from aparse import Parameter
from aparse.core import _empty


def test_utils_prefix_parameter():
    from aparse.utils import prefix_parameter, get_path

    p = Parameter(name='test', type=str)
    p2 = prefix_parameter(p, 'a.bb.ccc')
    assert get_path(p2, 'bb.ccc.test').name == 'test'


def test_utils_get_path_dict():
    from aparse.utils import get_path

    p = dict(bb=dict(ccc=dict(test='ok')))
    assert get_path(p, 'bb.ccc.test') == 'ok'
    assert get_path(p, 'bb.ccc.test2', default='ok2') == 'ok2'
    with pytest.raises(IndexError):
        get_path(p, 'bb.ccc.test2')


def test_utils_get_path_class():
    from aparse.utils import get_path

    p = namedtuple('k', 'bb')(namedtuple('k2', 'ccc')(namedtuple('k3', 'test')('ok')))
    assert get_path(p, 'bb.ccc.test') == 'ok'
    assert get_path(p, 'bb.ccc.test2', default='ok2') == 'ok2'
    with pytest.raises(IndexError):
        get_path(p, 'bb.ccc.test2')


def test_utils_get_empty():
    from aparse.utils import get_path

    with pytest.raises(IndexError):
        get_path(_empty, 'bb.ccc.test2')

    with pytest.raises(IndexError):
        get_path(None, 'bb.ccc.test2')


def test_get_parameters_no_parent():
    from aparse.utils import get_path, get_parameters

    class A:
        def __init__(test_a: str):
            pass

    class B(A):
        def __init__(test_b: str):
            pass

    params = get_parameters(B)
    assert get_path(params, 'test_b', None) is not None
    assert get_path(params, 'test_a', None) is None


def test_get_parameters_parent():
    from aparse.utils import get_path, get_parameters

    class A:
        def __init__(test_a: str):
            pass

    class B(A):
        def __init__(test_b: str, **kwargs):
            pass

    params = get_parameters(B)
    assert get_path(params, 'test_b', None) is not None
    assert get_path(params, 'test_a', None) is not None


def test_get_parameters_parent2():
    from aparse.utils import get_path, get_parameters

    class A:
        def __init__(test_a: str):
            pass

    class B(A):
        def __init__(test_b: str, **args):
            pass

    params = get_parameters(B)
    assert get_path(params, 'test_b', None) is not None
    assert get_path(params, 'test_a', None) is not None


def test_get_parameters_dataclass_default_factory():
    from aparse.utils import get_parameters

    @dataclass
    class A:
        test_a: int = field(default_factory=lambda: 5)

    params = get_parameters(A)
    assert params.find('test_a').default == 5


def test_consolidate_parameter_tree_different_type():
    from aparse.utils import get_parameters, merge_parameter_trees, consolidate_parameter_tree

    def a(test: str):
        pass

    def b(test: int):
        pass

    params = merge_parameter_trees(get_parameters(a), get_parameters(b))
    with pytest.raises(Exception):
        params = consolidate_parameter_tree(params)


def test_consolidate_parameter_tree_same_type():
    from aparse.utils import get_parameters, merge_parameter_trees, consolidate_parameter_tree

    def a(test: str):
        pass

    def b(test: str = 'test'):
        pass

    params = merge_parameter_trees(get_parameters(a), get_parameters(b))
    params = consolidate_parameter_tree(params)
    assert len(params.children) == 1
    assert params.find('test').default == 'test'
