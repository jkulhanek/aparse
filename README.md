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
```
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
