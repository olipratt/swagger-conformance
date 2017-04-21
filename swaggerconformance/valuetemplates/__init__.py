"""
This package provides access to two main classes of objects:

* `ValueFactory` for generating `ValueTemplate` instances
  matching the parameter values defines by a parameter entry in a swagger
  schema. This can be inherited from to generate new `ValueTemplate`
  instances matching custom parameters in a user's schema.
* The `ValueTemplate` itself and child classes used to generate
  hypothesis strategies for generating parameter values with certain
  constraints. Again, users may create new `ValueTemplate` subclasses
  to define their own new value types.
"""
from . import _valuetemplatefactory
from . import _valuetemplates
from ._valuetemplatefactory import *
from ._valuetemplates import *

__all__ = _valuetemplatefactory.__all__ + _valuetemplates.__all__
