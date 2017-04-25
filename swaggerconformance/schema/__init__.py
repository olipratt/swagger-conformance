"""
This package provides templates which can be generated from a Swagger schema to
represent parts of that schema which can later be filled in by generated
values.

It also exposes the `Primitive` interface, which is the type of object that is
passed to a `StrategyFactory` to generate values for.
"""
from ._api import Api
from ._operation import Operation
from ._parameter import Parameter
from ._primitive import Primitive

__all__ = ["Api", "Operation", "Parameter", "Primitive"]
