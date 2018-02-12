"""
Wrapper around a Swagger definition of a paramater for an operation.
"""
# This class exposes swagger format named properties which pylint objects to.
# There's also a few properties duplicated from the Parameter class it doesn't
# like, so disable that warning too, except it can't be disabled locally so
# has to be disabled globally.
# pylint: disable=invalid-name,too-many-public-methods
import logging

__all__ = ["Primitive"]


log = logging.getLogger(__name__)


class Primitive:
    """Wrapper around a primitive in a swagger schema.

    This may be a Parameter or a Schema Swagger object, either passed directly
    as a parameter to an operation as a child of one.

    Since a Swagger Items object may be a child of a Parameter or schema, treat
    that the same as well since it's sufficiently similar we don't care about
    the distinction. Items don't have names though, so be careful of that.

    :param swagger_definition: The swagger spec definition of this parameter.
    :type swagger_definition: pyswagger.spec.v2_0.objects.Parameter or
                              pyswagger.spec.v2_0.objects.Items or
                              pyswagger.spec.v2_0.objects.Schema
    """

    def __init__(self, swagger_definition):
        self._swagger_definition = self._resolve(swagger_definition)

    @staticmethod
    def _resolve(definition):
        """If the schema for this Primitive is a reference, dereference it."""
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
        """The name of this Primitive, if it has one.

        :rtype: str or None
        """
        return getattr(self._swagger_definition, 'name', None)

    @property
    def type(self):
        """The type of this Primitive.

        :rtype: str
        """
        return self._swagger_definition.type

    @property
    def format(self):
        """The format of this Primitive.

        :rtype: str or None
        """
        return self._swagger_definition.format

    @property
    def required(self):
        """Whether this Primitive is required.

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
        """The location of this Primitive - e.g. 'header' or 'body', or `None`
        if not a top-level primitive.

        :rtype: str or None
        """
        return getattr(self._swagger_definition, 'in', None)

    @property
    def items(self):
        """The Parameter elements of this Primitive if it's an array.

        :rtype: Primitive or None
        """
        items = self._swagger_definition.items
        return None if items is None else self.__class__(items)

    @property
    def properties(self):
        """The dict of Primitive elements of this Primitive if it's an object.

        :rtype: dict(str, Primitive) or None
        """
        # This attribute is only present on `Schema` objects.
        if not hasattr(self._swagger_definition, 'properties'):
            return None  # pragma: no cover - means called on wrong obect type
        return {prop_name: self.__class__(prop_value)
                for prop_name, prop_value in
                self._swagger_definition.properties.items()}

    @property
    def required_properties(self):
        """Set of required property names of this Primitive if it's an object.

        :rtype: set(str) or None
        """
        # This clashes with the name of the bool indicating if this is a
        # required parameter on a paramter object, so only use the value if
        # it's a list.
        reqd_props = getattr(self._swagger_definition, 'required', None)
        return set(reqd_props) if isinstance(reqd_props, list) else None

    @property
    def additionalProperties(self):
        """Whether this Primitive is a dict that accepts arbitrary entries.

        :rtype: bool or None
        """
        # This attribute is only present on `Schema` objects.
        if not hasattr(self._swagger_definition, 'additionalProperties'):
            return None  # pragma: no cover - means called on wrong obect type
        return self._swagger_definition.additionalProperties not in (None,
                                                                     False)

    @property
    def maxProperties(self):
        """The maximum number of properties in this Primitive if it's a dict.

        :rtype: int or None
        """
        if not hasattr(self._swagger_definition, 'maxProperties'):
            return None  # pragma: no cover - means called on wrong obect type
        return self._swagger_definition.maxProperties

    @property
    def minProperties(self):
        """The minimum number of properties in this Primitive if it's a dict.

        :rtype: int or None
        """
        if not hasattr(self._swagger_definition, 'minProperties'):
            return None  # pragma: no cover - means called on wrong obect type
        return self._swagger_definition.minProperties

    @property
    def maximum(self):
        """The maximum value of this Primitive.

        :rtype: float or None
        """
        return self._swagger_definition.maximum

    @property
    def exclusiveMaximum(self):
        """Whether the maximum value of this Primitive is allowed.

        :rtype: bool
        """
        return self._swagger_definition.exclusiveMaximum

    @property
    def minimum(self):
        """The minimum value of this Primitive.

        :rtype: float or None
        """
        return self._swagger_definition.minimum

    @property
    def exclusiveMinimum(self):
        """Whether the minimum value of this Primitive is allowed.

        :rtype: bool
        """
        return self._swagger_definition.exclusiveMinimum

    @property
    def multipleOf(self):
        """The value of this Primitive must be a multiple of this value.

        :rtype: float or None
        """
        return self._swagger_definition.multipleOf

    @property
    def maxLength(self):
        """The maximum length of this Primitive.

        :rtype: int or None
        """
        return self._swagger_definition.maxLength

    @property
    def minLength(self):
        """The minimum length of this Primitive.

        :rtype: int or None
        """
        return self._swagger_definition.minLength

    @property
    def pattern(self):
        """The regex pattern for this Primitive.

        :rtype: string or None
        """
        return self._swagger_definition.pattern

    @property
    def maxItems(self):
        """The maximum number of items in this Primitive if it's an array.

        :rtype: int or None
        """
        return self._swagger_definition.maxItems

    @property
    def minItems(self):
        """The minimum number of items in this Primitive if it's an array.

        :rtype: int or None
        """
        return self._swagger_definition.minItems

    @property
    def uniqueItems(self):
        """Whether the items in this Primitive are unique if it's an array.

        :rtype: bool
        """
        return self._swagger_definition.uniqueItems

    @property
    def enum(self):
        """List of valid values for this Primitive.

        :rtype: list or None
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
