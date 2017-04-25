"""
Factories for creating PrimitiveStrategys from swagger definitions.
"""
import logging
from collections import defaultdict

from . import primitivestrategies as ps

__all__ = ["StrategyFactory", "string_primitive_strategy"]


log = logging.getLogger(__name__)


def string_primitive_strategy(swagger_definition, factory):
    """Function for creating an appropriately formatted string value depending
    on the location of the string parameter.

    :param swagger_definition: The schema of the parameter to create.
    :type swagger_definition: schema.Primitive
    :rtype: PrimitiveStrategy
    """
    if swagger_definition.location == 'path':
        template = ps.URLPathStringStrategy(swagger_definition, factory)
    elif swagger_definition.location == 'header':
        template = ps.HTTPHeaderStringStrategy(swagger_definition, factory)
    else:
        template = ps.StringStrategy(swagger_definition, factory)
    return template


class StrategyFactory:
    """Factory for building `PrimitiveStrategy` from swagger definitions."""

    def __init__(self):
        self._map = {
            'boolean': defaultdict(lambda: ps.BooleanStrategy,
                                   [(None, ps.BooleanStrategy)]),
            'integer': defaultdict(lambda: ps.IntegerStrategy,
                                   [(None, ps.IntegerStrategy)]),
            'number': defaultdict(lambda: ps.FloatStrategy,
                                  [(None, ps.FloatStrategy)]),
            'file': defaultdict(lambda: ps.FileStrategy,
                                [(None, ps.FileStrategy)]),
            'array': defaultdict(lambda: ps.ArrayStrategy,
                                 [(None, ps.ArrayStrategy)]),
            'object': defaultdict(lambda: ps.ObjectStrategy,
                                  [(None, ps.ObjectStrategy)]),
            'string': defaultdict(lambda: string_primitive_strategy,
                                  [(None, string_primitive_strategy),
                                   ('byte', ps.BytesStrategy),
                                   ('date', ps.DateStrategy),
                                   ('date-time', ps.DateTimeStrategy),
                                   ('mask', ps.XFieldsHeaderStringStrategy),
                                   ('uuid', ps.UUIDStrategy)])
        }

    def _get(self, type_str, format_str):
        return self._map[type_str][format_str]

    def _set(self, type_str, format_str, creator):
        self._map[type_str][format_str] = creator

    def _set_default(self, type_str, creator):
        self._map[type_str].default_factory = lambda: creator

    def produce(self, swagger_definition):
        """Create a template for the value specified by the definition.

        :param swagger_definition: The schema of the parameter to create.
        :type swagger_definition: schema.Primitive
        :rtype: PrimitiveStrategy
        """
        log.debug("Creating value for: %r", swagger_definition)
        creator = self._get(swagger_definition.type, swagger_definition.format)
        value = creator(swagger_definition, self)

        assert value is not None, "Unsupported type, format: {}, {}".format(
            swagger_definition.type, swagger_definition.format)

        return value

    def register(self, type_str, format_str, creator):
        """Register a function to generate `PrimitiveStrategy` instances for
        this type and format pair.

        The function signature of the ``creator`` parameter must be:

        ``def fn(`` `schema.Primitive` , `StrategyFactory` ``) ->``
        `PrimitiveStrategy`

        :param type_str: The Swagger schema type to register for.
        :type type_str: str
        :param format_str: The Swagger schema format to register for.
        :type format_str: str
        :param creator: The function to create a `PrimitiveStrategy`.
        :type creator: callable
        """
        self._set(type_str, format_str, creator)

    def register_type_default(self, type_str, creator):
        """Register a function to generate `PrimitiveStrategy` instances for
        this type paired with any format with no other registered creator.

        The function signature of the ``creator`` parameter must be:

        ``def fn(`` `schema.Primitive` , `StrategyFactory` ``) ->``
        `PrimitiveStrategy`

        :param type_str: The Swagger schema type to register for.
        :type type_str: str
        :param creator: The function to create a `PrimitiveStrategy`.
        :type creator: callable
        """
        self._set_default(type_str, creator)
