"""
Templates for values of various data types.
"""
import logging
import math

import hypothesis.strategies as hy_st
from .. import strategies as sw_st

__all__ = ["ArrayTemplate", "ObjectTemplate", "ValueTemplate",
           "BooleanTemplate", "NumericTemplate", "IntegerTemplate",
           "FloatTemplate", "StringTemplate", "URLPathStringTemplate",
           "HTTPHeaderStringTemplate", "DateTemplate", "DateTimeTemplate",
           "UUIDTemplate", "FileTemplate"]


log = logging.getLogger(__name__)


class ArrayTemplate:
    """Template for an array value."""

    def __init__(self, max_items=None, min_items=None, unique_items=None):
        super().__init__()
        self._max_items = max_items
        self._min_items = min_items
        self._unique_items = unique_items

    def hypothesize(self, elements):
        """Return a hypothesis strategy defining this collection."""
        return hy_st.lists(elements=elements,
                           min_size=self._min_items,
                           max_size=self._max_items,
                           unique=self._unique_items)


class ObjectTemplate:
    """Template for a JSON object value."""
    # Limit on the number of additional properties to add to objects.
    # Setting this too high might cause data generation to time out.
    MAX_ADDITIONAL_PROPERTIES = 5

    def __init__(self, max_properties=None, min_properties=None,
                 additional_properties=False):
        super().__init__()
        self._max_properties = max_properties
        self._min_properties = min_properties
        self._additional_properties = additional_properties

    def hypothesize(self, required_properties, optional_properties):
        """Return a hypothesis strategy defining this collection.

        :type required_properties: dict
        :type optional_properties: dict
        """
        # The result must contain the specified propereties.
        result = sw_st.merge_optional_dict_strategy(required_properties,
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
                sw_st.json(),
                min_size=min_properties,
                max_size=max_properties)

            if self._max_properties is not None:
                result = sw_st.merge_dicts_max_size_strategy(
                    result, extra, self._max_properties)
            else:
                result = sw_st.merge_dicts_strategy(result, extra)

        return result


class ValueTemplate:
    """Template for a single value of any specified type."""

    def hypothesize(self):
        """Return a hypothesis strategy defining this value."""
        raise NotImplementedError("Abstract method")


class BooleanTemplate(ValueTemplate):
    """Template for a Boolean value."""

    def hypothesize(self):
        return hy_st.booleans()


class NumericTemplate(ValueTemplate):
    """Abstract template for a numeric value."""

    def __init__(self, maximum=None, exclusive_maximum=None,
                 minimum=None, exclusive_minimum=None,
                 multiple_of=None):
        super().__init__()
        if exclusive_maximum and (maximum is None):
            raise ValueError("Can't have exclusive max set and no max")
        if exclusive_minimum and (minimum is None):
            raise ValueError("Can't have exclusive min set and no min")
        self._maximum = maximum
        self._exclusive_maximum = exclusive_maximum
        self._minimum = minimum
        self._exclusive_minimum = exclusive_minimum
        self._multiple_of = multiple_of

    def hypothesize(self):
        raise NotImplementedError("Abstract method")


class IntegerTemplate(NumericTemplate):
    """Template for an integer value."""

    def __init__(self, maximum=None, exclusive_maximum=None,
                 minimum=None, exclusive_minimum=None,
                 multiple_of=None):
        super().__init__(maximum, exclusive_maximum,
                         minimum, exclusive_minimum, multiple_of)

    def hypothesize(self):
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


class FloatTemplate(NumericTemplate):
    """Template for a floating point value."""

    def __init__(self, maximum=None, exclusive_maximum=None,
                 minimum=None, exclusive_minimum=None,
                 multiple_of=None):
        super().__init__(maximum, exclusive_maximum,
                         minimum, exclusive_minimum, multiple_of)

    def hypothesize(self):
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


class StringTemplate(ValueTemplate):
    """Template for a string value."""

    def __init__(self, max_length=None, min_length=None,
                 pattern=None, enum=None,
                 blacklist_chars=None):
        super().__init__()
        self._max_length = max_length
        self._min_length = min_length
        self._pattern = pattern
        self._enum = enum
        self._blacklist_chars = blacklist_chars

    def hypothesize(self):
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


class URLPathStringTemplate(StringTemplate):
    """Template for a string value which must be valid in a URL path."""

    def __init__(self, max_length=None, min_length=None,
                 pattern=None, enum=None):
        if min_length is None:
            min_length = 1
        if min_length < 1:
            raise ValueError("Path parameters must be at least 1 char long")
        super().__init__(max_length=max_length, min_length=min_length,
                         pattern=pattern, enum=enum)


class HTTPHeaderStringTemplate(StringTemplate):
    """Template for a string value which must be valid in a HTTP header."""

    def __init__(self, max_length=None, min_length=None,
                 pattern=None, enum=None):
        # Heaved values are strings but cannot contain newlines.
        super().__init__(max_length=max_length, min_length=min_length,
                         pattern=pattern, enum=enum,
                         blacklist_chars=['\r', '\n'])

    def hypothesize(self):
        # Header values shouldn't have surrounding whitespace.
        return super().hypothesize().map(str.strip)

class DateTemplate(ValueTemplate):
    """Template for a Date value."""

    def hypothesize(self):
        return sw_st.dates()


class DateTimeTemplate(ValueTemplate):
    """Template for a Date-Time value."""

    def hypothesize(self):
        return sw_st.datetimes()


class UUIDTemplate(ValueTemplate):
    """Template for a UUID value."""

    def hypothesize(self):
        return hy_st.uuids()


class FileTemplate(ValueTemplate):
    """Template for a File value."""

    def hypothesize(self):
        return sw_st.files()
