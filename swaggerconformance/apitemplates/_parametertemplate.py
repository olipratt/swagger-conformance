"""
Template for parameters of a Swagger-defined API operation.
"""
import logging

__all__ = ["ParameterTemplate"]


log = logging.getLogger(__name__)


class ParameterTemplate:
    """A Swagger API operation parameter.

    :param swagger_definition: The swagger spec portion defining the parameter.
    :type swagger_definition: SwaggerDefinition
    """

    def __init__(self, swagger_definition):
        self._swagger_definition = swagger_definition

        self._items = None
        self._properties = None

    def __repr__(self):
        return "{}(name={!r}, type={!r}, format={!r}, required={!r})".format(
            self.__class__.__name__, self.name, self.type, self.format,
            self.required)

    def hypothesize(self, value_factory):
        """Generate a hypothesis strategy representing this parameter.

        :param value_factory: Factory to generate strategies for values.
        :type value_factory: swaggerconformance.valuetemplates.ValueFactory
        """
        value_template = value_factory.produce(self._swagger_definition)

        return value_template.hypothesize()

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

        :rtype: str or None
        """
        return self._swagger_definition.format

    @property
    def required(self):
        """Whether this parameter is required.

        :rtype: bool
        """
        return self._swagger_definition.required
