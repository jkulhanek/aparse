---
layout: default
title: API
nav_order: 5
has_children: true
permalink: api
---

# Utilities
{: .no_toc }

CSS utility classes come in handy when you to want to override default styles to create additional whitespace (margins/padding), correct unexpected shifts in font size or weight, add color, or hide (or show) something at a specific screen size.
{: .fs-6 .fw-300 }


---
layout: default
title: Introduction
nav_order: 1
permalink: /
---
# Introduction

{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

[Aparse](https://github.com/jkulhanek/aparse) is a python argparse extension with support for typing.
It has support for `argparse` and `click`
libraries. It uses function signatures to automatically register arguments to parsers.

The following features are currently supported:
- Arguments with `int`, `float`, `str`, `bool` values both with and without default value.
- List of `int`, `float`, `str`, `bool` types.
- Types with `from_str` method.
- `dataclass` arguments, where the dataclass is expanded into individual parameters
- Multi-level `dataclass` arguments.
- `argparse` and `click` libraries are fully supported.
- For `argparse`, when classes are used, it supports traversing inheritance chain.
- For `argparse`, custom prefixes can be used for groups of parameters.
- Callbacks before and after arguments are parsed.
- Conditional arguments, where the type of arguments depends on the value of another argument.


## Why aparse
**Why not argparse?**
Aparse does not force you to replace your argparse code. In fact, it was
designed to extend argparse. You can combine the original argparse code
and in some parts of the code, you can let aparse generate the arguments
automatically.

Furthermore, aparse allows you to use conditional parameter parsing, which
cannot be achieved with pure argparse.

**Why not click?**
Same as with argparse, aparse extends click in such a way, that you can
combine the original code with aparse. With aparse, you don't have to
decorate your commands with all options, but you can let aparse manage
them for you.

**Why not docopt?**
With docopt you have to keep documentation in sync with your code.
Aparse uses the signatures instead, which allows you to validate
your code with a typechecker.


## Installation
Install the library from pip:
```
$ pip install aparse
```

## Getting started
### Using argparse library
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

### Using click library
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

## License
[MIT](https://github.com/jkulhanek/aparse/blob/master/LICENSE)
