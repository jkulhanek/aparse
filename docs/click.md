---
layout: default
title: Using click
nav_order: 3
permalink: /click
---
# Using click

{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Simple command
Import `aparse.click` instead of `click` and let `aparse` register all
the arguments and options:
```python
# python main.py --arg1 test --arg2 4

from aparse import click

@click.command()
def example(arg1: str, arg2: int = 5):
    pass

example()
```

## Command group
When using `click.groups`:
```python
# python main.py example --arg1 test --arg2 4

from aparse import click

@click.group()
def main():
    pass

@main.command('example')
def example(arg1: str, arg2: int = 5):
    pass

main()
```

## Getting raw argparse arguments
If you need access to the raw arguments, you can use `aparse.AllArguments`,
in which case, the argparse arguments are passed as a dictionary.
```python
# python main.py --a 3

import argparse
from aparse import click, AllArguments

@click.command()
def example(ArgparseArguments: args, a: int = 5):
    pass

example()
```

## Using dataclasses as arguments
Dataclasses are expanded as other argparse arguments. You can
even have nested dataclasses.
```python
# python main.py --d1-test ok

@dataclass
class D1:
    test: str

@click.command()
def main(d1: D1):
    pass

main()
```

## List arguments
Lists can be used as arguments. In that case, the values are separated by commas.
```python
# python main.py --d 2,3 --e te,st

@click.command()
def main(d: List[int], e: List[str]):
    pass

main()
```

## Custom code to construct class from string
If needed, you can specify, how the argument's class instance
is constructed from a string argument.
```python
# python main.py --d test

class CS:
    def __init__(self, a):
        self.a = a

    @staticmethod
    def from_str(str_val):
        return CS(f'ok-{str_val}')

@click.command()
def main(d: CS):
    pass

main()
```

## Ignoring arguments
Arguments can be ignored as follows:
```python
# python main.py --k 3

@click.command(ignore={'m'})
def main(k: int = 1, m: float = 2.):
    return dict(k=k, m=m)

main()
```

## Registering callbacks before and after parse
You can use this functionality when you want to modify the
parser based on the input from the `parse_args` call or based
on the program's arguments. A typical use case is to condition
arguments based on the value of another argument.

One callback is `before_parse`, which gets the `aparse.Parameter` 
object (which describes how the argument will be parsed),
runtime instance, and a `kwargs` dictionary, which contains the
string values parsed from the `parse_args` call or from `sys.argv`.
The `before_parse` usually returns a new instance of `aparse.Parameter`.

The following example shows adding a new parameter if the value of
another parameter `k` is `3`.
```python
# python main.py --k 3

def callback(param, runtime, kwargs):
    if kwargs['k'] == '3':
        return Parameter(name='test', type=str, default_factory=lambda: 5)

@click.command(before_parse=callback)
def main(k: int = 1, **kwargs):
    # kwargs contains 'test'
    pass

main()
```

Other callback `after_parse` gets as its input `aparse.Parameter`,
raw arguments and parsed `kwargs`. It returns a modified
`kwargs`.
```python
# python main.py --k 3

def callback(param, arguments, kwargs):
    kwargs['k'] += 1
    return kwargs

@click.command(after_parse=callback)
def main(k: int = 1):
    pass

main()
```

## Conditional parsing
Aparse allows you to condition the argument type based on another argument's
value. In the following example, based on the '--k' argument value the type for
parameter k is chosen.
```python
# python main.py --k d2 --k-prop-d2 ok

from aparse import click

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
def main(k: DSwitch):
    # k will an instance of D2 in this example
    pass

main()
```

## Conditional parsing without prefix
Furthermore, you can choose not to include the parameter name in the
class properties.
```python
# python main.py --k d2 --prop-d2 ok

from aparse import click

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
def main(k: DSwitch):
    # k will an instance of D2 in this example
    pass

main()
```
