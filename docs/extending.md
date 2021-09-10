---
layout: default
title: Extending aparse
nav_order: 4
permalink: /extending
---
# Extending aparse

{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

You can extend the basic handling of the aparse library, e.g., to
add your own types. Implement your own `aparse.Handler` and register
it with `aparse.register_handler` decorator.

For example the following code is the handler used for parsing lists.
```python
from aparse import Handler, register_handler, ParameterWithPath

@register_handler
class SimpleListHandler(Handler):
    def _list_type(self, tp: Type):
        if getattr(tp, '__origin__', None) == list:
            tp = tp.__args__[0]
            if tp in (int, str, float):
                return tp
        return None

    def preprocess_parameter(self, parameter: ParameterWithPath) -> Tuple[bool, Union[Parameter, ParameterWithPath]]:
        if self._list_type(parameter.type) is not None:
            return True, dataclasses.replace(parameter, argument_type=str)
        return False, parameter

    def parse_value(self, parameter: ParameterWithPath, value: Any) -> Tuple[bool, Any]:
        list_type = self._list_type(parameter.type)
        if list_type is not None and isinstance(value, str):
            return True, list(map(list_type, value.split(',')))
        return False, value
```

