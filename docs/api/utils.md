---
layout: default
title: aparse.utils
parent: API
---
# Module aparse.utils

None

None

## Functions

    
### get_parameters

```python3
def get_parameters(
    obj: Any
) -> aparse.core.Parameter
```

    

    
### get_path

```python3
def get_path(
    obj,
    path,
    default=<object object at 0x7f04c6394f20>,
    _current_path=None
)
```

    

    
### ignore_parameters

```python3
def ignore_parameters(
    parameters,
    ignore
)
```

    

    
### is_type_compatible

```python3
def is_type_compatible(
    annotation,
    type2
)
```

    

    
### merge_parameter_defaults

```python3
def merge_parameter_defaults(
    parameters: aparse.core.Parameter,
    parameter_defaults: aparse.core.Parameter,
    soft_defaults: bool = False
) -> aparse.core.Parameter
```

    

    
### merge_parameter_trees

```python3
def merge_parameter_trees(
    *args,
    force=True
)
```

    

    
### prefix_parameter

```python3
def prefix_parameter(
    parameter,
    prefix,
    container_type=None
)
```

    

    
### walk_multiple

```python3
def walk_multiple(
    callback: Callable[[List[aparse.core.ParameterWithPath], List[aparse.core.ParameterWithPath]], Union[aparse.core.ParameterWithPath, NoneType]],
    parameter: aparse.core.Parameter,
    *others: aparse.core.Parameter
) -> aparse.core.Parameter
```
