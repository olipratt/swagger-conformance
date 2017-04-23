"""
Wrapper around a Swagger definition of a paramater for an operation.
"""
import logging

__all__ = ["SwaggerParameter"]


log = logging.getLogger(__name__)


class SwaggerParameter:
    """Wrapper around a parameter to pass to an operation on an endpoint.

    This may be a `Parameter` or a `Schema` object, either passed directly as
    a parameter to an operation as a child of one.

    Since a Swagger `Items` object may be a child of a `Parameter`, treat that
    as a parameter as well since it's sufficiently similar we don't care about
    the distinction. `Items` don't have names though, so be careful of that.

    :param swagger_app: The API the parameter is part of.
    :type swagger_app: pyswagger.core.App
    :param swagger_definition: The swagger spec definition of this parameter.
    :type swagger_definition: pyswagger.spec.v2_0.objects.Parameter or
                              pyswagger.spec.v2_0.objects.Items or
                              pyswagger.spec.v2_0.objects.Schema
    """

    def __init__(self, swagger_definition):
        self._swagger_definition = self._resolve(swagger_definition)

    def _resolve(self, definition):
        """If the schema for this parameter is a reference, dereference it."""
        while getattr(definition, 'ref_obj', None) is not None:
            log.debug("New definition is: %r", definition)
            definition = definition.ref_obj

        return definition

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self.name,
                                             self.type)

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
    def required(self):
        """Whether this parameter is required.

        :rtype: bool
        """
        # If not specified in the underlying definition (or not applicable),
        # then the default is that the value is required.
        # This also clashes with the name of the list of required fields in a
        # schema object, so only use the value if it's a Boolean.
        required = getattr(self._swagger_definition, 'required', None)
        return required if isinstance(required, bool) else True

    @property
    def location(self):
        """The location of this parameter - e.g. 'header' or 'body', or `None`
        if not a top-level parameter.

        :rtype: str or None
        """
        return getattr(self._swagger_definition, 'in', None)

    @property
    def items(self):
        """The Parameter elements of this Parameter if it's an array.

        :rtype: SwaggerParameter or None
        """
        items = self._swagger_definition.items
        return None if items is None else self.__class__(items)

    @property
    def properties(self):
        """The dict of Parameter elements of this Parameter if it's an object.

        :rtype: dict(str, SwaggerParameter) or None
        """
        # This attribute is only present on `Schema` objects.
        if not hasattr(self._swagger_definition, 'properties'):
            return None  # pragma: no cover - means called on wrong obect type
        return {prop_name: self.__class__(prop_value)
                for prop_name, prop_value in
                self._swagger_definition.properties.items()}

    @property
    def required_properties(self):
        """Set of required property names of this Parameter if it's an object.

        :rtype: set(str) or None
        """
        # This clashes with the name of the bool indicating if this is a
        # required parameter on a paramter object, so only use the value if
        # it's a list.
        reqd_props = getattr(self._swagger_definition, 'required', None)
        return set(reqd_props) if isinstance(reqd_props, list) else None

    @property
    def additionalProperties(self):
        """Whether this paramater is a dict that accepts arbitrary entries.

        :rtype: bool
        """
        # This attribute is only present on `Schema` objects.
        if not hasattr(self._swagger_definition, 'additionalProperties'):
            return None  # pragma: no cover - means called on wrong obect type
        return self._swagger_definition.additionalProperties not in (None,
                                                                     False)

    @property
    def maxProperties(self):
        """The maximum number of properties in this parameter if it's a dict.

        :rtype: int
        """
        if not hasattr(self._swagger_definition, 'maxProperties'):
            return None  # pragma: no cover - means called on wrong obect type
        return self._swagger_definition.maxProperties

    @property
    def minProperties(self):
        """The minimum number of properties in this parameter if it's a dict.

        :rtype: int
        """
        if not hasattr(self._swagger_definition, 'minProperties'):
            return None  # pragma: no cover - means called on wrong obect type
        return self._swagger_definition.minProperties

    @property
    def maximum(self):
        """The maximum value of this parameter.

        :rtype: float
        """
        return self._swagger_definition.maximum

    @property
    def exclusiveMaximum(self):
        """Whether the maximum value of this parameter is allowed.

        :rtype: bool
        """
        return self._swagger_definition.exclusiveMaximum

    @property
    def minimum(self):
        """The minimum value of this parameter.

        :rtype: float
        """
        return self._swagger_definition.minimum

    @property
    def exclusiveMinimum(self):
        """Whether the minimum value of this parameter is allowed.

        :rtype: bool
        """
        return self._swagger_definition.exclusiveMinimum

    @property
    def multipleOf(self):
        """The value of this parameter must be a multiple of this value.

        :rtype: float or None
        """
        return self._swagger_definition.multipleOf

    @property
    def maxLength(self):
        """The maximum length of this parameter.

        :rtype: int
        """
        return self._swagger_definition.maxLength

    @property
    def minLength(self):
        """The minimum length of this parameter.

        :rtype: int
        """
        return self._swagger_definition.minLength

    @property
    def pattern(self):
        """The regex pattern for this parameter.

        :rtype: string
        """
        return self._swagger_definition.pattern

    @property
    def maxItems(self):
        """The maximum number of items in this parameter if it's an array.

        :rtype: int
        """
        return self._swagger_definition.maxItems

    @property
    def minItems(self):
        """The minimum number of items in this parameter if it's an array.

        :rtype: int
        """
        return self._swagger_definition.minItems

    @property
    def uniqueItems(self):
        """Whether the items in this parameter are unique if it's an array.

        :rtype: bool
        """
        return self._swagger_definition.uniqueItems

    @property
    def enum(self):
        """List of valid values for this paramater.

        :rtype: list
        """
        return self._swagger_definition.enum

    @property
    def _pyswagger_definition(self):
        """The underlying pyswagger definition - useful elsewhere internally
        but not expected to be referenced external to the package.

        :rtype: pyswagger.spec.v2_0.objects.Parameter or
                pyswagger.spec.v2_0.objects.Items or
                pyswagger.spec.v2_0.objects.Schema
        """
        return self._swagger_definition
