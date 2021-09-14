---
layout: default
title: aparse.click
parent: API
---
# Module aparse.click

None

None

## Functions

    
### command

```python3
def command(
    name=None,
    cls=None,
    before_parse=None,
    after_parse=None,
    soft_defaults=False,
    **kwargs
)
```

    

    
### group

```python3
def group(
    name=None,
    cls=None,
    **attrs
)
```

    

    
### option

```python3
def option(
    *param_decls,
    **attrs
)
```

    
Attaches an option to the command.  All positional arguments are

passed as parameter declarations to :class:`Option`; all keyword
arguments are forwarded unchanged (except ``cls``).
This is equivalent to creating an :class:`Option` instance manually
and attaching it to the :attr:`Command.params` list.

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| cls | None | the option class to instantiate.  This defaults to
:class:`Option`. | None |

## Classes

### ClickRuntime

```python3
class ClickRuntime(
    fn,
    soft_defaults=False
)
```

#### Ancestors (in MRO)

* aparse.core.Runtime

#### Methods

    
#### add_parameter

```python3
def add_parameter(
    self,
    argument_name,
    argument_type,
    required=True,
    help='',
    default=<object object at 0x7f41a04bef50>,
    choices=None
)
```

    

    
#### add_parameters

```python3
def add_parameters(
    self,
    parameters: aparse.core.Parameter
)
```

    

    
#### read_defaults

```python3
def read_defaults(
    self,
    parameters: aparse.core.Parameter
)
```
