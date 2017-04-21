"""
Factories for creating ValueTemplates from swagger definitions.
"""
import logging
from collections import defaultdict

from . import _valuetemplates as vts

__all__ = ["ValueFactory"]


log = logging.getLogger(__name__)


class ValueFactory:
    """Factory for building `ValueTemplate` from swagger definitions."""

    def __init__(self):
        self._map = {
            'boolean': defaultdict(lambda: self._create_bool_value,
                                   [(None, self._create_bool_value)]),
            'integer': defaultdict(lambda: self._create_integer_value,
                                   [(None, self._create_integer_value)]),
            'number': defaultdict(lambda: self._create_float_value,
                                  [(None, self._create_float_value)]),
            'file': defaultdict(lambda: self._create_file_value,
                                [(None, self._create_file_value)]),
            'array': defaultdict(lambda: self._create_array_value,
                                 [(None, self._create_array_value)]),
            'object': defaultdict(lambda: self._create_object_value,
                                  [(None, self._create_object_value)]),
            'string': defaultdict(lambda: self._create_default_string_value,
                                  [(None, self._create_string_value),
                                   ('date', self._create_date_value),
                                   ('date-time', self._create_datetime_value),
                                   ('uuid', self._create_uuid_value)])
        }

    def _get(self, type_str, format_str):
        return self._map[type_str][format_str]

    def _set(self, type_str, format_str, creator):
        self._map[type_str][format_str] = creator

    def _set_default(self, type_str, creator):
        self._map[type_str].default_factory = lambda: creator

    def create_value(self, swagger_definition):
        """Create a template for the value specified by the definition.

        :param swagger_definition: The schema of the parameter to
        :type swagger_definition: apitemplates.SwaggerParameter
        :rtype: ValueTemplate
        """
        log.debug("Creating value for: %r", swagger_definition)
        creator = self._get(swagger_definition.type, swagger_definition.format)
        value = creator(swagger_definition)

        assert value is not None, "Unsupported type, format: {}, {}".format(
            swagger_definition.type, swagger_definition.format)

        return value

    def register(self, type_str, format_str, creator):
        """Register a function to generate `ValueTemplate` instances for this
        type and format pair.

        The function signature of the ``creator`` parameter must be:

        ``def fn(`` `apitemplates.SwaggerParameter` ``) ->`` `ValueTemplate`

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

        ``def fn(`` `apitemplates.SwaggerParameter` ``) ->`` `ValueTemplate`

        :param type_str: The Swagger schema type to register for.
        :type type_str: str
        :param creator: The function to create a `ValueTemplate`.
        :type creator: callable
        """
        self._set_default(type_str, creator)

    def _create_bool_value(self, swagger_definition):
        return vts.BooleanTemplate()

    def _create_integer_value(self, swagger_definition):
        return vts.IntegerTemplate(
            maximum=swagger_definition.maximum,
            exclusive_maximum=swagger_definition.exclusiveMaximum,
            minimum=swagger_definition.minimum,
            exclusive_minimum=swagger_definition.exclusiveMinimum,
            multiple_of=swagger_definition.multipleOf)

    def _create_float_value(self, swagger_definition):
        return vts.FloatTemplate(
            maximum=swagger_definition.maximum,
            exclusive_maximum=swagger_definition.exclusiveMaximum,
            minimum=swagger_definition.minimum,
            exclusive_minimum=swagger_definition.exclusiveMinimum,
            multiple_of=swagger_definition.multipleOf)

    def _create_date_value(self, swagger_definition):
        return vts.DateTemplate()

    def _create_datetime_value(self, swagger_definition):
        return vts.DateTimeTemplate()

    def _create_uuid_value(self, swagger_definition):
        return vts.UUIDTemplate()

    def _create_file_value(self, swagger_definition):
        return vts.FileTemplate()

    def _create_xfields_header_value(self, swagger_definition):
        return vts.XFieldsHeaderStringTemplate()

    def _create_string_value(self, swagger_definition):
        if swagger_definition.location == 'path':
            template_type = vts.URLPathStringTemplate
        elif swagger_definition.location == 'header':
            template_type = vts.HTTPHeaderStringTemplate
        else:
            template_type = vts.StringTemplate
        return template_type(max_length=swagger_definition.maxLength,
                             min_length=swagger_definition.minLength,
                             pattern=swagger_definition.pattern,
                             enum=swagger_definition.enum)

    def _create_default_string_value(self, swagger_definition):
        if (swagger_definition.location == "header" and
                swagger_definition.name == "X-Fields"):
            return self._create_xfields_header_value(swagger_definition)
        else:
            creator = self._get(swagger_definition.type, None)
            return creator(swagger_definition)

    def _create_array_value(self, swagger_definition):
        return vts.ArrayTemplate(
            max_items=swagger_definition.maxItems,
            min_items=swagger_definition.minItems,
            unique_items=swagger_definition.uniqueItems)

    def _create_object_value(self, swagger_definition):
        log.debug("Properties: %r", swagger_definition.properties)
        # If there are no fixed properties then allow arbitrary ones to be
        # added.
        additional = (swagger_definition.additionalProperties or
                      len(swagger_definition.properties) == 0)
        log.debug("Allow additional properties? %r", additional)
        return vts.ObjectTemplate(
            max_properties=swagger_definition.maxProperties,
            min_properties=swagger_definition.minProperties,
            additional_properties=additional)
