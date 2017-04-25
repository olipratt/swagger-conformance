"""
This package enables easy testing of Swagger Spec defined APIs using property
based tests and by generating paramter values meeting the specification.

This top-level package exposes functions for basic API tests just requiring
access to the API schema.

Subpackages and modules then provide classes and functions for finer grain
control over value generation and test procedures.
"""
from ._basictests import api_conformance_test, operation_conformance_test

__all__ = ["api_conformance_test", "operation_conformance_test"]
