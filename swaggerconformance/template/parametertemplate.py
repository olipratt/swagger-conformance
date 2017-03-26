"""
Templates for parameter and model parts of a Swagger-defined API which can be
passed to specific API operations adhering to the definition.
"""
import logging

from .valuetemplatefactory import (BaseValueFactory, ParameterValueFactory,
                                   ModelValueFactory)


log = logging.getLogger(__name__)


class BaseParameterTemplate:
    """Common base class for Swagger API operation paramters."""
    VALUE_FACTORY = BaseValueFactory

    def __init__(self, swagger_app, swagger_definition):
        self._swagger_app = swagger_app
        self._swagger_definition = swagger_definition
        self._children = None
        self._value_template = None

        self._populate_value()
        self._populate_children()

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self.name,
                                             self.type)

    def _populate_children(self):
        if self.type == 'array':
            self._children = self.__class__(self._swagger_app,
                                            self._swagger_definition.items)

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
    def children(self):
        """The children of this parameter - may be `None` if there are none.
        :rtype: ParameterTemplate or None
        """
        return self._children


class ParameterTemplate(BaseParameterTemplate):
    """Template for a parameter to pass to an operation on an endpoint.

    Since a Swagger `Items` object maybe a child of a `Parameter`, model that
    as a parameter as well since it's sufficiently similar we don't care about
    the distinction. `Items` don't have names though, so be careful of that.

    :type swagger_app: pyswagger.App
    :type swagger_definition: pyswagger.spec.v2_0.objects.Parameter or
                              pyswagger.spec.v2_0.objects.Items
    """
    VALUE_FACTORY = ParameterValueFactory


class ModelTemplate(BaseParameterTemplate):
    """Template for a generic parameter, which may be one of many types,
    defining the model it follows.

    In the Swagger/OpenAPI world, this maps to a `Schema Object`.

    :type swagger_app: pyswagger.App
    :type swagger_definition: pyswagger.spec.v2_0.objects.Schema
    """
    VALUE_FACTORY = ModelValueFactory

    def __init__(self, swagger_app, swagger_definition):
        super().__init__(swagger_app, self._resolve_schema(swagger_app,
                                                           swagger_definition))

    def _resolve_schema(self, app, schema):
        """If the schema for this model is a reference, dereference it."""
        ref = getattr(schema, '$ref')
        log.debug("Ref is: %r", ref)
        if ref is not None:
            schema = app.resolve(ref)
        log.debug("Schema: %r", schema)
        log.debug("Schema name: %r", schema.name)

        return schema

    def _populate_children(self):
        if self.type == 'object':
            log.debug("Properties: %r", self._swagger_definition.properties)
            self._children = {prop_name: self.__class__(self._swagger_app,
                                                        prop_value)
                              for prop_name, prop_value in
                              self._swagger_definition.properties.items()}

        super()._populate_children()
