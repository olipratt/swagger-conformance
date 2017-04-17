"""
This package provides templates which can be generated from a Swagger schema to
represent parts of that schema which can later be filled in by generated
values.

It also exposes the `SwaggerParameter` interface, which is the type of
object that is passed to a `ValueFactory` to generate values for.
"""
from ._apitemplate import APITemplate
from ._operationtemplate import OperationTemplate
from ._parametertemplate import ParameterTemplate
from ._swaggerparameter import SwaggerParameter

__all__ = ["APITemplate", "OperationTemplate", "ParameterTemplate",
           "SwaggerParameter"]
