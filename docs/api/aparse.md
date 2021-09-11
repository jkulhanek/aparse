---
layout: default
title: aparse
nav_order: 1
permalink: /api/aparse
---
# Module aparse

None

None

## Sub-modules

* [aparse.argparse](argparse/)
* [aparse.click](click/)
* [aparse.core](core/)
* [aparse.utils](utils/)

## Variables

```python3
Literal
```

## Functions

    
### AllArguments

```python3
def AllArguments(
    x
)
```

    

    
### ConditionalType

```python3
def ConditionalType(
    typename,
    fields=None,
    *,
    prefix: bool = True,
    **kwargs
)
```

    
ConditionalType allows aparse to condition its choices for a

specific parameter based on an argument.
Usage::
    class Model(ConditionalType):
        gpt2: GPT2
        resnet: ResNet
The type info can be accessed via the Model.__annotations__ dict,
and the Model.__required_keys__ and Model.__optional_keys__ frozensets.
ConditionalType supports two additional equivalent forms:
    Model = ConditionalType('Model', gpt2=GPT2, resnet=ResNet)
    Model = ConditionalType('Model', dict(gpt2=GPT2, resnet=ResNet))
The class syntax is only supported in Python 3.6+, while two other
syntax forms work for Python 2.7 and 3.2+

    
### add_argparse_arguments

```python3
def add_argparse_arguments(
    _fn=None,
    *,
    ignore: Set[str] = None,
    before_parse: Callable[[argparse.ArgumentParser, Dict[str, Any]], argparse.ArgumentParser] = None,
    after_parse: Callable[[argparse.Namespace, Dict[str, Any]], Dict[str, Any]] = None
)
```

    
Extends function or class with "add_argparse_arguments", "from_argparse_arguments", and "bind_argparse_arguments" methods.

"add_argparse_arguments" adds arguments to the argparse.ArgumentParser instance.
"from_argparse_arguments" takes the argparse.Namespace instance obtained by calling parse.parse_args(), parses them and calls
    original function or constructs the class
"bind_argparse_arguments" just parses the arguments into a kwargs dictionary, but does not call the original function. Instead,
    the parameters are returned.

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| ignore | None | Set of parameters to ignore when inspecting the function signature | None |
| before_parse | None | Callback to be called before parser.parse_args() | None |
| after_parse | None | Callback to be called before "from_argparse_arguments" calls the function and updates the kwargs.
Returns: The original function extended with other functions. | None |

    
### register_handler

```python3
def register_handler(
    handler
)
```

    

## Classes

### Handler

```python3
class Handler(
    /,
    *args,
    **kwargs
)
```

#### Descendants

* aparse._handlers.DefaultHandler
* aparse._handlers.AllArgumentsHandler
* aparse._handlers.SimpleListHandler
* aparse._handlers.FromStrHandler
* aparse._handlers.ConditionalTypeHandler

#### Methods

    
#### add_parameter

```python3
def add_parameter(
    self,
    parameter: aparse.core.ParameterWithPath,
    parser: aparse.core.Runtime
) -> bool
```

    

    
#### bind

```python3
def bind(
    self,
    parameter: aparse.core.ParameterWithPath,
    args: Dict[str, Any],
    children: List[Tuple[aparse.core.Parameter, Any]]
) -> Tuple[bool, Any]
```

    

    
#### parse_value

```python3
def parse_value(
    self,
    parameter: aparse.core.ParameterWithPath,
    value: Any
) -> Tuple[bool, Any]
```

    

    
#### preprocess_parameter

```python3
def preprocess_parameter(
    self,
    parameter: aparse.core.ParameterWithPath
) -> Tuple[bool, aparse.core.ParameterWithPath]
```

    

### Parameter

```python3
class Parameter(
    name: Union[str, NoneType],
    type: Union[Type, NoneType],
    help: str = '',
    children: List[ForwardRef('Parameter')] = <factory>,
    default_factory: Union[Callable[[], Any], NoneType] = None,
    choices: Union[List[Any], NoneType] = None,
    argument_type: Union[Any, NoneType] = None,
    _argument_name: Union[Tuple[str], NoneType] = None
)
```

#### Class variables

```python3
argument_type
```

```python3
choices
```

```python3
default_factory
```

```python3
help
```

#### Instance variables

```python3
default
```

#### Methods

    
#### enumerate_parameters

```python3
def enumerate_parameters(
    self
)
```

    

    
#### find

```python3
def find(
    self,
    name: str
) -> Union[ForwardRef('Parameter'), NoneType]
```

    

    
#### replace

```python3
def replace(
    self,
    **kwargs
)
```

    

    
#### walk

```python3
def walk(
    self,
    fn: Callable[[ForwardRef('ParameterWithPath'), List[Any]], Any]
)
```

    

### ParameterWithPath

```python3
class ParameterWithPath(
    parameter: aparse.core.Parameter,
    parent: Union[ForwardRef('ParameterWithPath'), NoneType] = None
)
```

#### Class variables

```python3
parent
```

#### Instance variables

```python3
argument_name
```

```python3
argument_type
```

```python3
children
```

```python3
choices
```

```python3
default
```

```python3
default_factory
```

```python3
full_name
```

```python3
help
```

```python3
name
```

```python3
type
```

#### Methods

    
#### find

```python3
def find(
    self,
    name
)
```

    

    
#### replace

```python3
def replace(
    self,
    **kwargs
)
```
