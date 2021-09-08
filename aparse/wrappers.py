from functools import partial
from argparse import ArgumentParser, Namespace
from typing import Set, Callable, Any, Dict
from ._lib import add_argparse_arguments as _add_argparse_arguments
from ._lib import get_parameters, preprocess_argparse_parameter, ignore_parameters
from ._lib import from_argparse_arguments as _from_argparse_arguments
from ._lib import bind_argparse_arguments as _bind_argparse_arguments


def add_argparse_arguments(
        _fn=None, *,
        ignore: Set[str] = None,
        before_parse: Callable[[ArgumentParser, Dict[str, Any]], ArgumentParser] = None,
        after_parse: Callable[[Namespace, Dict[str, Any]], Dict[str, Any]] = None):
    '''
    Extends function or class with "add_argparse_arguments", "from_argparse_arguments", and "bind_argparse_arguments" methods.
    "add_argparse_arguments" adds arguments to the argparse.ArgumentParser instance.
    "from_argparse_arguments" takes the argparse.Namespace instance obtained by calling parse.parse_args(), parses them and calls
        original function or constructs the class
    "bind_argparse_arguments" just parses the arguments into a kwargs dictionary, but does not call the original function. Instead,
        the parameters are returned.

    Arguments:
        ignore: Set of parameters to ignore when inspecting the function signature
        before_parse: Callback to be called before parser.parse_args()
        after_parse: Callback to be called before "from_argparse_arguments" calls the function and updates the kwargs.

    Returns: The original function extended with other functions.
    '''
    def wrap(fn):
        parameters = get_parameters(fn).walk(preprocess_argparse_parameter)
        if ignore is not None:
            parameters = ignore_parameters(parameters, ignore)
        setattr(fn, 'add_argparse_arguments', partial(_add_argparse_arguments, parameters, _before_parse=before_parse))
        setattr(fn, 'from_argparse_arguments', partial(_from_argparse_arguments, parameters, fn, _after_parse=after_parse))
        setattr(fn, 'bind_argparse_arguments', partial(_bind_argparse_arguments, parameters, after_parse=after_parse))
        return fn

    if _fn is not None:
        return wrap(_fn)
    return wrap
