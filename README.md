# aparse
![build](https://img.shields.io/github/workflow/status/jkulhanek/aparse/Upload%20Python%20Package)
![pypi](https://img.shields.io/pypi/v/aparse.svg)

Python argparse extension with support for typing.

## Getting started
Install the library from pip:
```
$ pip install aparse
```

Extend a function with `@add_argparse_arguments` decorator to add arguments automatically:
```python
import argparse
from aparse import add_argparse_arguments

@add_argparse_arguments()
def example(arg1: str, arg2: int = 5):
    pass

parser = argparse.ArgumentParser()
parser = example.add_argparse_arguments(parser)
args = parser.parse_args()

# Call example with args
example.from_argparse_arguments(args)
```

Extend a class with `@add_argparse_arguments` decorator to construct it automatically:
```python
import argparse
from aparse import add_argparse_arguments

@add_argparse_arguments()
class Example:
    def __init__(self, arg1: str, arg2: int = 5):
        pass

parser = argparse.ArgumentParser()
parser = Example.add_argparse_arguments(parser)
args = parser.parse_args()

# Construct Example with args
instance = Example.from_argparse_arguments(args)
```

## Advanced usage
### Using class inheritance
Arguments are automatically added from all base classes 
if kwargs or args arguments are used in the constructor.
```python
import argparse
from aparse import add_argparse_arguments

class Parent:
    def __init__(self, arg3: str = 'test'):
        pass

@add_argparse_arguments()
class Example(Parent):
    def __init__(arg1: str, arg2: int = 5, **kwargs):
        super().__init__(**kwargs)

parser = argparse.ArgumentParser()
parser = Example.add_argparse_arguments(parser)
args = parser.parse_args()

# Construct Example with args
instance = Example.from_argparse_arguments(args)
```

### Using arguments with the same name
Arguments can be reused if they share the same name.
If the types are same and none or only one of them has a default parameter
the arguments are merged automatically. If both arguments have a different type
or a different values, exception is raised by default. You can prevent this
behavior by using `soft_defaults=True` when calling `add_argparse_arguments`.
```python
import argparse
from aparse import add_argparse_arguments

@add_argparse_arguments()
def example1(arg1: str, arg2: int = 5):
    pass

@add_argparse_arguments()
def example2(arg1: str = 'test', arg2: int = 5):
    pass

parser = argparse.ArgumentParser()
parser = example1.add_argparse_arguments(parser)
parser = example2.add_argparse_arguments(parser)
args = parser.parse_args()

# Call example1 and example2 with args
example1.from_argparse_arguments(args)
example2.from_argparse_arguments(args)
```

### Using prefixes
Prefixes can be used to separate otherwise incompatible parameters.
```python
import argparse
from aparse import add_argparse_arguments

@add_argparse_arguments()
def example1(arg1: str, arg2: int = 3):
    pass

@add_argparse_arguments()
def example2(arg1: str = 'test', arg2: int = 5):
    pass

parser = argparse.ArgumentParser()
parser = example1.add_argparse_arguments(parser, prefix='ex1')
parser = example2.add_argparse_arguments(parser, prefix='ex2')
args = parser.parse_args()

# Call example1 and example2 with args
example1.from_argparse_arguments(args, _prefix='ex1')
example2.from_argparse_arguments(args, _prefix='ex2')
```

### Getting raw argparse arguments
If you need access to the raw arguments, you can use `aparse.ArgparseArguments`,
in which case, the argparse arguments are passed as a dictionary.
```python
import argparse
from aparse import add_argparse_arguments, ArgparseArguments

@add_argparse_arguments()
def example(ArgparseArguments: args):
    pass

parser = argparse.ArgumentParser()
parser = example.add_argparse_arguments(parser)
args = parser.parse_args()

# Call example with args
example.from_argparse_arguments(args)
```

### Using nested dataclasses as arguments
Dataclasses are expanded as other argparse arguments. You can
even have nested dataclasses.
```python
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
d2 = D2.from_argparse_arguments(args)
```

### List arguments
Lists can be used as arguments. In that case, the values are separated by commas.
```python
@add_argparse_arguments()
def test_fn(d: List[int], e: List[str]):
    return d, e

argparser = ArgumentParser()
test_fn.add_argparse_arguments(argparser)
args = argparser.parse_args(['--d', '2,3', '--e', 'te,st'])
d, e = test_fn.from_argparse_arguments(args)
```

### Custom code to construct class from string
If needed, you can specify, how the argument's class instance
is constructed from a string argument.
```python
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
d = test_fn.from_argparse_arguments(args)
```

### Getting the parsed arguments
In order to obtain the parsed kwargs without calling your function,
use the `bind_argparse_arguments` function.
```python
@add_argparse_arguments()
def testfn(k: int = 1, m: float = 2.):
    return dict(k=k, m=m)

argparser = ArgumentParser()
argparser = testfn.add_argparse_arguments(argparser)
args = argparser.parse_args(['--k', '3'])
kwargs = testfn.bind_argparse_arguments(args)
```

### Passing other arguments to from\_argparse\_arguments
By defaults, aparse forwards any arguments passed to the 
`from_argparse_arguments` function to the original function.
If the name is the same as an already existing argparse argument,
its value is replaced by the value passed to the `from_argparse_arguments` function.
```python
@add_argparse_arguments()
def testfn(x, k: int = 1, m: float = 2.):
    return dict(k=k, m=m, x=x)

argparser = ArgumentParser()
argparser = testfn.add_argparse_arguments(argparser)
args = argparser.parse_args(['--k', '3'])
testfn.from_argparse_arguments(args, 'test', m=5)
```

### Ignoring arguments
Arguments can be ignored as follows:
```python
@add_argparse_arguments(ignore={'m'})
def testfn(k: int = 1, m: float = 2.):
    return dict(k=k, m=m)

argparser = ArgumentParser()
argparser = testfn.add_argparse_arguments(argparser)
args = argparser.parse_args(['--k', '3'])
testfn.from_argparse_arguments(args)
```


### Extending aparse
You can extend the basic handling of the aparse library, e.g., to
add your own types. Implement your own `aparse.Handler` and register
it with `aparse.register_handler` decorator.

For example the following code is the handler used for parsing lists.
```python
from aparse import Handler, register_handler

@register_handler
class SimpleListHandler(Handler):
    def _list_type(self, tp: Type):
        if getattr(tp, '__origin__', None) == list:
            tp = tp.__args__[0]
            if tp in (int, str, float):
                return tp
        return None

    def preprocess_argparse_parameter(self, parameter: Parameter) -> Type:
        if self._list_type(parameter.type) is not None:
            return True, dataclasses.replace(parameter, argument_type=str)
        return False, parameter

    def parse_value(self, parameter: Parameter, value: Any) -> Any:
        list_type = self._list_type(parameter.type)
        if list_type is not None and isinstance(value, str):
            return True, list(map(list_type, value.split(',')))
        return False, value
```

### Registering callbacks before and after parse
You can use this functionality when you want to modify the
parser based on the input from the `parse_args` call or based
on the program's arguments. A typical use case is to condition
arguments based on the value of another argument.

One callback is `before_parse`, which gets the `aparse.Parameter` 
object (which describes how the argument will be parsed),
parser instance, and a `kwargs` dictionary, which contains the
string values parsed from the `parse_args` call or from `sys.argv`.
The `before_parse` usually returns a new instance of `aparse.Parameter`.

The following example shows adding a new parameter if the value of
another parameter `k` is `3`.
```python
def callback(param, parser, kwargs):
    if kwargs['k'] == '3':
        return Parameter(name='test', type=str, default_factory=lambda: 5)

@add_argparse_arguments(before_parse=callback)
def testfn(k: int = 1, **kwargs):
    return kwargs

argparser = ArgumentParser()
argparser = testfn.add_argparse_arguments(argparser)
args = argparser.parse_args(['--k', '3'])
testfn.from_argparse_arguments(args)
assert d['test'] == 5
```

Other callback `after_parse` gets as its input `aparse.Parameter`,
`argparse.Namespace` and parsed `kwargs`. It returns a modified
`kwargs`.
```python
def callback(param, namespace, kwargs):
    kwargs[k] += 1
    return kwargs

@add_argparse_arguments(after_parse=callback)
def testfn(k: int = 1):
    assert k == 4

argparser = ArgumentParser()
argparser = testfn.add_argparse_arguments(argparser)
args = argparser.parse_args(['--k', '3'])
testfn.from_argparse_arguments(args)
```

### Conditional parsing
Conditional parsing can be implemented with `after_parse` and
`before_parse` callbacks.
