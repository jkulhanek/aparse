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
    default=<object object at 0x7f3c8d110f50>,
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
