"""
Factories for creating ValueTemplates from swagger definitions.
"""
import logging

from . import valuetemplates as vts


log = logging.getLogger(__name__)


class ValueFactory:
    """Common factory for building ValueTemplates from swagger definitions."""

    def create_value(self, swagger_definition):
        """Create a ValueTemplate for the value specified by the definition.

        :type swagger_definition: swaggerparameter.SwaggerParameter
        """
        value = None
        if swagger_definition.type == 'boolean':
            value = self._create_bool_value(swagger_definition)
        elif swagger_definition.type == 'integer':
            value = self._create_integer_value(swagger_definition)
        elif swagger_definition.type == 'number':
            value = self._create_float_value(swagger_definition)
        elif swagger_definition.type == 'string':
            if swagger_definition.format == 'date':
                value = self._create_date_value(swagger_definition)
            elif swagger_definition.format == 'date-time':
                value = self._create_datetime_value(swagger_definition)
            elif swagger_definition.format == 'uuid':
                value = self._create_uuid_value(swagger_definition)
            else:
                value = self._create_string_value(swagger_definition)
        elif swagger_definition.type == 'file':
            value = self._create_file_value(swagger_definition)
        elif swagger_definition.type == 'array':
            value = self._create_array_value(swagger_definition)
        elif swagger_definition.type == 'object':
            return self._create_object_value(swagger_definition)

        if value is None:
            raise ValueError("Unsupported type, format: {}, {}".format(
                swagger_definition.type, swagger_definition.format))

        return value

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
