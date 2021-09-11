---
layout: default
title: aparse.utils
parent: API
---
# Module aparse.utils

None

None

## Functions

    
### consolidate_parameter_tree

```python3
def consolidate_parameter_tree(
    parameters: aparse.core.Parameter,
    soft_defaults: bool = False
) -> aparse.core.Parameter
```

    

    
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
    default=<object object at 0x7f3c8d110f50>,
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

    

    
### merge_parameter_trees

```python3
def merge_parameter_trees(
    *args
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
