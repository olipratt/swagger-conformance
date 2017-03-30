"""
Templates for parameter and model parts of a Swagger-defined API which can be
passed to specific API operations adhering to the definition.
"""
import logging

from .valuetemplatefactory import ValueFactory

log = logging.getLogger(__name__)


class ParameterTemplate:
    """Common class for Swagger API operation parameters."""
    VALUE_FACTORY = ValueFactory

    def __init__(self, swagger_definition):
        self._swagger_definition = swagger_definition
        self._value_template = None
        self._items = None
        self._properties = None

        self._populate_value()
        self._populate_children()

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self.name,
                                             self.type)

    def _populate_children(self):
        if self.type == 'array':
            self._items = self.__class__(self._swagger_definition.items)
        if self.type == 'object':
            log.debug("Properties: %r", self._swagger_definition.properties)
            self._properties = {prop_name: self.__class__(prop_value)
                                for prop_name, prop_value in
                                self._swagger_definition.properties.items()}

    def _populate_value(self):
        self._value_template = self.VALUE_FACTORY.create_value(
            self._swagger_definition)

    @property
    def name(self):
        """The name of this parameter, if it has one.
        :rtype: str or None
        """
        return getattr(self._swagger_definition, 'name', None)

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
    def value_template(self):
        """The template for the value of this parameter.
        :rtype: valuetemplates.ValueTemplate
        """
        return self._value_template

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
