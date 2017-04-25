"""
This package provides access to two main classes of objects:

* `StrategyFactory` for generating `PrimitiveStrategy` instances
  matching the parameter values defines by a parameter entry in a swagger
  schema. This can be inherited from to generate new `PrimitiveStrategy`
  instances matching custom parameters in a user's schema.
* The `PrimitiveStrategy` itself and child classes used to generate
  hypothesis strategies for generating parameter values with certain
  constraints. Again, users may create new `PrimitiveStrategy` subclasses
  to define their own new value types.
"""
from ._strategyfactory import StrategyFactory, string_primitive_strategy

__all__ = ["StrategyFactory", "string_primitive_strategy"]
