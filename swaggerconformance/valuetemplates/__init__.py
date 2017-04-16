"""
This package provides access to two main classes of objects:

* :class:`ValueFactory` for generating :class:`ValueTemplate` instances
  matching the parameter values defines by a parameter entry in a swagger
  schema. This can be inherited from to generate new :class:`ValueTemplate`
  instances matching custom parameters in a user's schema.
* The :class:`ValueTemplate` itself and child classes used to generate
  hypothesis strategies for generating parameter values with certain
  constraints. Again, users may create new :class:`ValueTemplate` subclasses
  to define their own new value types.
"""
from ._valuetemplatefactory import ValueFactory
from ._valuetemplates import *
from . import _valuetemplates

__all__ = ["ValueFactory"] + _valuetemplates.__all__
