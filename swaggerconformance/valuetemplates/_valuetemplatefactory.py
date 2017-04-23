"""
Factories for creating ValueTemplates from swagger definitions.
"""
import logging
from collections import defaultdict

from . import _valuetemplates as vts

__all__ = ["ValueFactory", "create_string_value"]


log = logging.getLogger(__name__)


def create_string_value(swagger_definition, factory):
    """Function for creating an appropriately formatted string value depending
    on the location of the string parameter.

    :param swagger_definition: The schema of the parameter to create.
    :type swagger_definition: apitemplates.SwaggerParameter
    :rtype: ValueTemplate
    """
    if swagger_definition.location == 'path':
        template = vts.URLPathStringTemplate(swagger_definition, factory)
    elif swagger_definition.location == 'header':
        template = vts.HTTPHeaderStringTemplate(swagger_definition, factory)
    else:
        template = vts.StringTemplate(swagger_definition, factory)
    return template


class ValueFactory:
    """Factory for building `ValueTemplate` from swagger definitions."""

    def __init__(self):
        self._map = {
            'boolean': defaultdict(lambda: vts.BooleanTemplate,
                                   [(None, vts.BooleanTemplate)]),
            'integer': defaultdict(lambda: vts.IntegerTemplate,
                                   [(None, vts.IntegerTemplate)]),
            'number': defaultdict(lambda: vts.FloatTemplate,
                                  [(None, vts.FloatTemplate)]),
            'file': defaultdict(lambda: vts.FileTemplate,
                                [(None, vts.FileTemplate)]),
            'array': defaultdict(lambda: vts.ArrayTemplate,
                                 [(None, vts.ArrayTemplate)]),
            'object': defaultdict(lambda: vts.ObjectTemplate,
                                  [(None, vts.ObjectTemplate)]),
            'string': defaultdict(lambda: self._create_default_string_value,
                                  [(None, create_string_value),
                                   ('byte', vts.BytesTemplate),
                                   ('date', vts.DateTemplate),
                                   ('date-time', vts.DateTimeTemplate),
                                   ('uuid', vts.UUIDTemplate)])
        }

    def _get(self, type_str, format_str):
        return self._map[type_str][format_str]

    def _set(self, type_str, format_str, creator):
        self._map[type_str][format_str] = creator

    def _set_default(self, type_str, creator):
        self._map[type_str].default_factory = lambda: creator

    def create_value(self, swagger_definition):
        """Create a template for the value specified by the definition.

        :param swagger_definition: The schema of the parameter to create.
        :type swagger_definition: apitemplates.SwaggerParameter
        :rtype: ValueTemplate
        """
        log.debug("Creating value for: %r", swagger_definition)
        creator = self._get(swagger_definition.type, swagger_definition.format)
        value = creator(swagger_definition, self)

        assert value is not None, "Unsupported type, format: {}, {}".format(
            swagger_definition.type, swagger_definition.format)

        return value

    def register(self, type_str, format_str, creator):
        """Register a function to generate `ValueTemplate` instances for this
        type and format pair.

        The function signature of the ``creator`` parameter must be:

        ``def fn(`` `apitemplates.SwaggerParameter` , `ValueFactory` ``) ->``
        `ValueTemplate`

        :param type_str: The Swagger schema type to register for.
        :type type_str: str
        :param format_str: The Swagger schema format to register for.
        :type format_str: str
        :param creator: The function to create a `ValueTemplate`.
        :type creator: callable
        """
        self._set(type_str, format_str, creator)

    def register_type_default(self, type_str, creator):
        """Register a function to generate `ValueTemplate` instances for this
        type paired with any format with no other registered creator.

        The function signature of the ``creator`` parameter must be:

        ``def fn(`` `apitemplates.SwaggerParameter` , `ValueFactory` ``) ->``
        `ValueTemplate`

        :param type_str: The Swagger schema type to register for.
        :type type_str: str
        :param creator: The function to create a `ValueTemplate`.
        :type creator: callable
        """
        self._set_default(type_str, creator)

    def _create_default_string_value(self, swagger_definition, _):
        if (swagger_definition.location == "header" and
                swagger_definition.name == "X-Fields"):
            creator = vts.XFieldsHeaderStringTemplate
        else:
            creator = self._get(swagger_definition.type, None)

        return creator(swagger_definition, self)
