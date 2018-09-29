"""
Strategies for values of various data types.
"""
# The classes in this file ahve a single public method by design.
# pylint: disable=too-few-public-methods
import logging
import math

import hypothesis.strategies as hy_st
from . import basestrategies as base_st

__all__ = ["PrimitiveStrategy", "BooleanStrategy", "NumericStrategy",
           "IntegerStrategy", "FloatStrategy", "StringStrategy",
           "URLPathStringStrategy", "HTTPHeaderStringStrategy",
           "XFieldsHeaderStringStrategy", "DateStrategy", "DateTimeStrategy",
           "UUIDStrategy", "FileStrategy", "ArrayStrategy", "ObjectStrategy"]


log = logging.getLogger(__name__)


class PrimitiveStrategy:
    """Strategy for a single value of any specified type.

    :param swagger_definition: The Swagger spec for this parameter.
    :type swagger_definition: schema.Primitive
    :param factory: The factory used to generate child `PrimitiveStrategy` s.
    :type factory: strategies.StrategyFactory
    """

    def __init__(self, swagger_definition, factory):
        self._swagger_definition = swagger_definition
        self._factory = factory

    def strategy(self):
        """Return a hypothesis strategy defining this value."""
        raise NotImplementedError("Abstract method")


class BooleanStrategy(PrimitiveStrategy):
    """Strategy for a Boolean value."""

    def strategy(self):
        return hy_st.booleans()


class NumericStrategy(PrimitiveStrategy):
    """Abstract template for a numeric value."""

    def __init__(self, swagger_definition, factory):
        super().__init__(swagger_definition, factory)
        assert not (swagger_definition.exclusiveMaximum and
                    (swagger_definition.maximum is None)), \
            "Can't have exclusive max set and no max"
        assert not (swagger_definition.exclusiveMinimum and
                    (swagger_definition.minimum is None)), \
            "Can't have exclusive min set and no min"
        self._maximum = swagger_definition.maximum
        self._exclusive_maximum = swagger_definition.exclusiveMaximum
        self._minimum = swagger_definition.minimum
        self._exclusive_minimum = swagger_definition.exclusiveMinimum
        self._multiple_of = swagger_definition.multipleOf

    def strategy(self):
        raise NotImplementedError("Abstract method")


class IntegerStrategy(NumericStrategy):
    """Strategy for an integer value."""

    def strategy(self):
        # Note that hypotheis requires integer bounds, but we may be provided
        # with float values.
        inclusive_max = self._maximum
        if inclusive_max is not None:
            inclusive_max = (int(self._maximum - 1)
                             if self._exclusive_maximum else
                             int(self._maximum))
            if self._multiple_of is not None:
                inclusive_max = math.floor(inclusive_max /
                                           int(self._multiple_of))
        inclusive_min = self._minimum
        if inclusive_min is not None:
            inclusive_min = (int(self._minimum + 1)
                             if self._exclusive_minimum else
                             int(self._minimum))
            if self._multiple_of is not None:
                inclusive_min = math.ceil(inclusive_min /
                                          int(self._multiple_of))
        strategy = hy_st.integers(min_value=inclusive_min,
                                  max_value=inclusive_max)
        if self._multiple_of is not None:
            strategy = strategy.map(lambda x: x * self._multiple_of)

        return strategy


class FloatStrategy(NumericStrategy):
    """Strategy for a floating point value."""

    def strategy(self):
        if self._multiple_of is not None:
            maximum = self._maximum
            if maximum is not None:
                maximum = math.floor(maximum / self._multiple_of)
            minimum = self._minimum
            if minimum is not None:
                minimum = math.ceil(minimum / self._multiple_of)
            strategy = hy_st.integers(min_value=minimum, max_value=maximum)
            strategy = strategy.map(lambda x: x * self._multiple_of)
        else:
            strategy = hy_st.floats(min_value=self._minimum,
                                    max_value=self._maximum)
        if self._exclusive_maximum:
            strategy = strategy.filter(lambda x: x < self._maximum)
        if self._exclusive_minimum:
            strategy = strategy.filter(lambda x: x > self._minimum)

        return strategy


class StringStrategy(PrimitiveStrategy):
    """Strategy for a string value."""

    def __init__(self, swagger_definition, factory, blacklist_chars=None):
        super().__init__(swagger_definition, factory)
        self._max_length = swagger_definition.maxLength
        self._min_length = swagger_definition.minLength
        self._enum = swagger_definition.enum
        self._pattern = swagger_definition.pattern
        self._blacklist_chars = blacklist_chars

    def strategy(self):
        if self._enum is not None:
            return hy_st.sampled_from(self._enum)

        alphabet = None
        if self._blacklist_chars:
            alphabet = hy_st.characters(
                blacklist_characters=self._blacklist_chars)
        strategy = hy_st.text(alphabet=alphabet,
                              min_size=self._min_length,
                              max_size=self._max_length)

        return strategy


class BytesStrategy(PrimitiveStrategy):
    """Strategy for a bytes string value.

    Assume the lengths refer to the number of bytes, rather than the length of
    some representation of them.
    """

    def __init__(self, swagger_definition, factory):
        super().__init__(swagger_definition, factory)
        self._max_length = swagger_definition.maxLength
        self._min_length = swagger_definition.minLength
        self._enum = swagger_definition.enum

        if self._min_length is None:
            self._min_length = 1
        assert self._min_length >= 1, "Byte parameters must be at least 1 byte"

    def strategy(self):
        if self._enum is not None:
            return hy_st.sampled_from(self._enum)

        strategy = hy_st.binary(min_size=self._min_length,
                                max_size=self._max_length)

        return strategy


class URLPathStringStrategy(StringStrategy):
    """Strategy for a string value which must be valid in a URL path."""

    def __init__(self, swagger_definition, factory):
        super().__init__(swagger_definition, factory)
        if self._min_length is None:
            self._min_length = 1
        assert self._min_length >= 1, "Path parameters must be at least 1 char"


class HTTPHeaderStringStrategy(StringStrategy):
    """Strategy for a string value which must be valid in a HTTP header."""

    def __init__(self, swagger_definition, factory):
        # Header values are strings but cannot contain newlines.
        super().__init__(
            swagger_definition, factory, blacklist_chars=['\r', '\n'])

    def strategy(self):
        # Header values shouldn't have surrounding whitespace.
        return super().strategy().map(str.strip)


class XFieldsHeaderStringStrategy(PrimitiveStrategy):
    """Strategy for a string value which must be valid in the X-Fields header.

    The ``X-Fields`` parameter lets you specify a mask of fields to be returned
    by the application. The format is a comma-separated list of fields to
    return, enclosed by curly-brackets, which can be nested. So for example:
    ``{name, age, pets{name}}``. There is also a special value of ``*`` meaning
    'all remaining fields', and it can be provided alone as ``*`` or inserted
    into a mask of the above format instead of a field name.

    We could generate random values for this header that match the allowed
    syntax, but:

    - as far as I can see, this field is a `Flast-RESTPlus` special,
    - this is implemented by the Swagger API framework, so not exciting to
      exercise,
    - there's a risk of just generating values which are rejected continually
      and so reducing the effectiveness of the testing of other fields.

    Therefore, we just return either ``''`` or ``*`` for this parameter as they
    are safe values that shouldn't interfere with other testing.
    """

    def strategy(self):
        return hy_st.sampled_from(("*", ''))


class DateStrategy(PrimitiveStrategy):
    """Strategy for a Date value."""

    def strategy(self):
        return hy_st.dates()


class DateTimeStrategy(PrimitiveStrategy):
    """Strategy for a Date-Time value."""

    def strategy(self):
        return hy_st.datetimes()


class UUIDStrategy(PrimitiveStrategy):
    """Strategy for a UUID value."""

    def strategy(self):
        return hy_st.uuids()


class FileStrategy(PrimitiveStrategy):
    """Strategy for a File value."""

    def strategy(self):
        return base_st.files()


class ArrayStrategy(PrimitiveStrategy):
    """Strategy for an array collection."""

    def __init__(self, swagger_definition, factory):
        super().__init__(swagger_definition, factory)

        self._elements = self._factory.produce(self._swagger_definition.items)

        self._max_items = swagger_definition.maxItems
        self._min_items = swagger_definition.minItems
        self._unique_items = swagger_definition.uniqueItems

    def strategy(self):
        """Return a hypothesis strategy defining this collection."""
        return hy_st.lists(elements=self._elements.strategy(),
                           min_size=self._min_items,
                           max_size=self._max_items,
                           unique=self._unique_items)


class ObjectStrategy(PrimitiveStrategy):
    """Strategy for a JSON object collection.

    `MAX_ADDITIONAL_PROPERTIES` is a limit on the number of additional
    properties to add to objects. Setting this too high might cause data
    generation to time out.
    """
    MAX_ADDITIONAL_PROPERTIES = 5

    def __init__(self, swagger_definition, factory):
        super().__init__(swagger_definition, factory)

        self._properties = {prop_name: self._factory.produce(prop_defn)
                            for prop_name, prop_defn in
                            self._swagger_definition.properties.items()}

        additional = (swagger_definition.additionalProperties or
                      len(swagger_definition.properties) == 0)
        log.debug("Allow additional properties? %r", additional)
        self._max_properties = swagger_definition.maxProperties
        self._min_properties = swagger_definition.minProperties
        self._additional_properties = additional

    def strategy(self):
        """Return a hypothesis strategy defining this collection, including
        random additional properties if the object supports them.

        Will add only up to `MAX_ADDITIONAL_PROPERTIES` extra values to
        prevent data generation taking too long and timing out.

        :param required_properties: The required fields in the generated dict.
        :type required_properties: dict
        :param optional_properties: The optional fields in the generated dict.
        :type optional_properties: dict
        """
        required_properties = {
            name: field.strategy()
            for name, field in self._properties.items()
            if name in self._swagger_definition.required_properties}
        optional_properties = {
            name: field.strategy()
            for name, field in self._properties.items()
            if name not in self._swagger_definition.required_properties}

        # The result must contain the specified propereties.
        result = base_st.merge_optional_dict_strategy(required_properties,
                                                      optional_properties)

        # If we allow arbitrary additional properties, create a dict with some
        # then update it with the fixed ones to ensure they are retained.
        if self._additional_properties:
            # Generate enough to stay within the allowed bounds, but don't
            # generate more than a fixed maximum.
            min_properties = (0 if self._min_properties is None else
                              self._min_properties)
            min_properties = max(0, min_properties - len(required_properties))
            max_properties = (self.MAX_ADDITIONAL_PROPERTIES
                              if self._max_properties is None else
                              self._max_properties)
            max_properties = min(self.MAX_ADDITIONAL_PROPERTIES,
                                 max_properties - len(required_properties))
            max_properties = max(max_properties, min_properties)
            log.debug("Determined max, min extra properties: %r, %r",
                      max_properties, min_properties)
            forbidden_prop_names = set(required_properties.keys() &
                                       optional_properties.keys())
            extra = hy_st.dictionaries(
                hy_st.text().filter(lambda x: x not in forbidden_prop_names),
                base_st.json(),
                min_size=min_properties,
                max_size=max_properties)

            if self._max_properties is not None:
                merge = base_st.merge_dicts_max_size_strategy
                result = merge(  # pylint: disable=no-value-for-parameter
                    result, extra, self._max_properties
                )
            else:
                result = base_st.merge_dicts_strategy(result, extra)

        return result
