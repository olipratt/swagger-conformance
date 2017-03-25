"""
Templates for values of various data types.
"""
import logging
import datetime
import io
import urllib.parse
import math

import hypothesis.strategies as hy_st


log = logging.getLogger(__name__)


JSON_STRATEGY = hy_st.recursive(
    hy_st.floats() | hy_st.booleans() | hy_st.text() | hy_st.none(),
    lambda children: hy_st.dictionaries(hy_st.text(), children),
    max_leaves=5
)

JSON_OBJECT_STRATEGY = hy_st.dictionaries(hy_st.text(), JSON_STRATEGY)

DATE_STRATEGY = hy_st.builds(
    datetime.date.fromordinal,
    hy_st.integers(min_value=1, max_value=datetime.date.max.toordinal())
)

TIME_STRATEGY = hy_st.builds(
    datetime.time,
    hour=hy_st.integers(min_value=0, max_value=23),
    minute=hy_st.integers(min_value=0, max_value=59),
    second=hy_st.integers(min_value=0, max_value=59),
    microsecond=hy_st.integers(min_value=0, max_value=999999)
)

DATETIME_STRATEGY = hy_st.builds(datetime.datetime.combine,
                                 DATE_STRATEGY,
                                 TIME_STRATEGY)

FILE_STRATEGY = hy_st.builds(io.BytesIO,
                             hy_st.binary()).map(lambda x: {'data': x})

CHARS_NO_RETURN_STRATEGY = hy_st.characters(blacklist_characters=['\r', '\n'])


TYPE_BOOLEAN = 'boolean'
TYPE_INTEGER = 'integer'
TYPE_FLOAT = 'float'
TYPE_STRING = 'string'
TYPE_ARRAY = 'array'
TYPE_OBJECT = 'object'
TYPE_DATE = 'date'
TYPE_DATETIME = 'date-time'
TYPE_FILE = 'file'


class ValueTemplate:
    """Template for a single value of any specified type."""

    def __init__(self, type_name, format_name):
        self._type = type_name
        self._format = format_name

    @property
    def type(self):
        return self._type

    @property
    def format(self):
        return self._format

    def hypothesize(self):
        """Return a hypothesis strategy defining this value."""
        raise NotImplementedError("Abstract method")


class BooleanTemplate(ValueTemplate):
    """Template for a Boolean value."""

    def __init__(self):
        super().__init__(TYPE_BOOLEAN, None)

    def hypothesize(self):
        return hy_st.booleans()


class NumericTemplate(ValueTemplate):
    """Template for a numeric value."""

    def __init__(self, type_name, format_name,
                 maximum=None, exclusive_maximum=None,
                 minimum=None, exclusive_minimum=None,
                 multiple_of=None):
        super().__init__(type_name, format_name)
        if exclusive_maximum and (maximum is None):
            raise ValueError("Can't have exclusive max set and no max")
        if exclusive_minimum and (minimum is None):
            raise ValueError("Can't have exclusive min set and no min")
        self._maximum = maximum
        self._exclusive_maximum = exclusive_maximum
        self._minimum = minimum
        self._exclusive_minimum = exclusive_minimum
        self._multiple_of = multiple_of


class IntegerTemplate(NumericTemplate):
    """Template for an integer value."""

    def __init__(self,
                 maximum=None, exclusive_maximum=None,
                 minimum=None, exclusive_minimum=None,
                 multiple_of=None):
        super().__init__(TYPE_INTEGER, None, maximum, exclusive_maximum,
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

    def __init__(self,
                 maximum=None, exclusive_maximum=None,
                 minimum=None, exclusive_minimum=None,
                 multiple_of=None):
        super().__init__(TYPE_FLOAT, None, maximum, exclusive_maximum,
                         minimum, exclusive_minimum, multiple_of)

    def hypothesize(self):
        if self._multiple_of is not None:
            maximum = self._maximum
            if maximum is not None:
                maximum = math.floor(maximum / self._multiple_of)
            minimum = self._minimum
            if minimum is not None:
                minimum = math.ceil(minimum / self._multiple_of)
            strategy = hy_st.floats(min_value=minimum, max_value=maximum)
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
        super().__init__(TYPE_STRING, None)
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
        super().__init__(max_length=max_length, min_length=min_length,
                         pattern=pattern, enum=enum)

    def hypothesize(self):
        return super().hypothesize().map(lambda x: urllib.parse.quote(x,
                                                                      safe=''))


class HTTPHeaderStringTemplate(StringTemplate):
    """Template for a string value which must be valid in a HTTP header."""

    def __init__(self, max_length=None, min_length=None,
                 pattern=None, enum=None):
        super().__init__(max_length=max_length, min_length=min_length,
                         pattern=pattern, enum=enum,
                         blacklist_chars=['\r', '\n'])

    def hypothesize(self):
        return super().hypothesize().map(str.strip)

class DateTemplate(ValueTemplate):
    """Template for a Date value."""

    def __init__(self):
        super().__init__(TYPE_DATE, None)

    def hypothesize(self):
        return DATE_STRATEGY


class DateTimeTemplate(ValueTemplate):
    """Template for a Date-Time value."""

    def __init__(self):
        super().__init__(TYPE_DATETIME, None)

    def hypothesize(self):
        return DATETIME_STRATEGY


class FileTemplate(ValueTemplate):
    """Template for a File value."""

    def __init__(self):
        super().__init__(TYPE_FILE, None)

    def hypothesize(self):
        return FILE_STRATEGY


class ArrayTemplate(ValueTemplate):
    """Template for an array value."""

    def __init__(self, max_items=None, min_items=None, unique_items=None):
        super().__init__(TYPE_ARRAY, None)
        self._max_items = max_items
        self._min_items = min_items
        self._unique_items = unique_items

    def hypothesize(self, elements):
        return hy_st.lists(elements=elements,
                           min_size=self._min_items,
                           max_size=self._max_items,
                           unique=self._unique_items)


class ObjectTemplate(ValueTemplate):
    """Template for a JSON object value."""

    def __init__(self, max_properties=None, min_properties=None,
                 additional_properties=False):
        super().__init__(TYPE_OBJECT, None)
        self._max_properties = max_properties
        self._min_properties = min_properties
        self._additional_properties = additional_properties

    def hypothesize(self, properties):
        # The result must contain the specified propereties.
        result = hy_st.fixed_dictionaries(properties)

        # If we allow arbitrary additional properties, create a dict with some
        # then update it with the fixed ones to ensure they are retained.
        if self._additional_properties:
            # Generate enough to stay within the allowed bounds, but don't
            # generate
            min_properties = (0 if self._min_properties is None else
                              self._min_properties)
            min_properties = max(0, min_properties - len(properties))
            max_properties = (5 if self._max_properties is None else
                              self._max_properties)
            max_properties = min(5, max_properties - len(properties))
            max_properties = max(max_properties, min_properties)
            extra = hy_st.dictionaries(hy_st.text(),
                                       JSON_STRATEGY,
                                       min_size=min_properties,
                                       max_size=max_properties)

            result = hy_st.builds(lambda x, y: x.update(y), extra, result)

        return result
