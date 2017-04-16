"""
Templates for parameter and model parts of a Swagger-defined API which can be
passed to specific API operations adhering to the definition.
"""
import logging

__all__ = ["ParameterTemplate"]


log = logging.getLogger(__name__)


class ParameterTemplate:
    """Common class for Swagger API operation parameters.

    :param swagger_definition: The swagger spec portion defining the parameter.
    :type swagger_definition: SwaggerParameter
    """

    def __init__(self, swagger_definition):
        self._swagger_definition = swagger_definition

        self._items = None
        self._properties = None

        self._populate_children()

    def __repr__(self):
        return "{}(name={!r}, type={!r}, required={!r})".format(
            self.__class__.__name__, self.name, self.type, self.required)

    def _populate_children(self):
        if self.type == 'array':
            self._items = self.__class__(self._swagger_definition.items)
        if self.type == 'object':
            log.debug("Properties: %r", self._swagger_definition.properties)
            self._properties = {prop_name: self.__class__(prop_value)
                                for prop_name, prop_value in
                                self._swagger_definition.properties.items()}

    def hypothesize(self, value_factory):
        """Generate a hypothesis strategy representing this parameter.

        :param value_factory: Factory to generate strategies for values.
        :type value_factory: swaggerconformance.valuetemplates.ValueFactory
        """
        value_template = value_factory.create_value(self._swagger_definition)

        if self.type == 'array':
            elements = self.items.hypothesize(value_factory)
            result = value_template.hypothesize(elements)
        elif self.type == 'object':
            reqd_props = {name: parameter.hypothesize(value_factory)
                          for name, parameter in self.properties.items()
                          if name in self.required_properties}
            opt_props = {name: parameter.hypothesize(value_factory)
                         for name, parameter in self.properties.items()
                         if name not in self.required_properties}
            result = value_template.hypothesize(reqd_props, opt_props)
        else:
            result = value_template.hypothesize()

        return result

    @property
    def name(self):
        """The name of this parameter, if it has one.

        :rtype: str or None
        """
        return self._swagger_definition.name

    @property
    def type(self):
        """The type of this parameter.

        :rtype: str
        """
        return self._swagger_definition.type

    @property
    def format(self):
        """The format of this parameter.

        :rtype: str
        """
        return self._swagger_definition.format

    @property
    def required(self):
        """Whether this parameter is required.

        :rtype: bool
        """
        return self._swagger_definition.required

    @property
    def items(self):
        """The children of this parameter if it's an array - `None` otherwise.

        :rtype: ParameterTemplate or None
        """
        return self._items

    @property
    def properties(self):
        """The children of this parameter if it's a dict - `None` otherwise.

        :rtype: dict(str, ParameterTemplate) or None
        """
        return self._properties

    @property
    def required_properties(self):
        """List of required property names of this parameter if it's an dict.

        :rtype: list(str) or None
        """
        return self._swagger_definition.required_properties
