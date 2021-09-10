from aparse import Parameter


def test_utils_prefix_parameter():
    from aparse.utils import prefix_parameter, get_path

    p = Parameter(name='test', type=str)
    p2 = prefix_parameter(p, 'a.bb.ccc')
    assert get_path(p2, 'bb.ccc.test').name == 'test'
