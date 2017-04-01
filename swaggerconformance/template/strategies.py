"""
Extra hypothesis strategies built from those in hypothesis.strategies.
"""
import logging
import datetime
import io

import hypothesis.strategies as hy_st


log = logging.getLogger(__name__)


# Generates JSON which can be passed e.g. to json.dumps.
JSON_STRATEGY = hy_st.recursive(
    hy_st.floats() | hy_st.booleans() | hy_st.text() | hy_st.none(),
    lambda children: hy_st.dictionaries(hy_st.text(), children),
    max_leaves=5
)

# Generates JSON objects.
JSON_OBJECT_STRATEGY = hy_st.dictionaries(hy_st.text(), JSON_STRATEGY)

# Generates datetime.date objects.
DATE_STRATEGY = hy_st.builds(
    datetime.date.fromordinal,
    hy_st.integers(min_value=1, max_value=datetime.date.max.toordinal())
)

# Generates datetime.time objects.
TIME_STRATEGY = hy_st.builds(
    datetime.time,
    hour=hy_st.integers(min_value=0, max_value=23),
    minute=hy_st.integers(min_value=0, max_value=59),
    second=hy_st.integers(min_value=0, max_value=59),
    microsecond=hy_st.integers(min_value=0, max_value=999999)
)

# Generates datetime.datetime objects.
DATETIME_STRATEGY = hy_st.builds(datetime.datetime.combine,
                                 DATE_STRATEGY,
                                 TIME_STRATEGY)

# Generated dictionaries in the format required by pyswagger to provide file
# contents for a swagger parameter.
FILE_STRATEGY = hy_st.builds(io.BytesIO,
                             hy_st.binary()).map(lambda x: {'data': x})


def combined_dicts_strategy(required_fields, optional_fields):
    """Combine dicts of required and optional strategies into one.
    :type required_fields: dict
    :type optional_fields: dict
    """
    optional_keys = hy_st.sets(hy_st.sampled_from(optional_fields.keys()))
    selected_optionals = hy_st.builds(
        lambda dictionary, keys: {key: dictionary[key] for key in keys},
        hy_st.fixed_dictionaries(optional_fields),
        optional_keys)
    result = hy_st.builds(lambda x, y: {**x, **y},
                          hy_st.fixed_dictionaries(required_fields),
                          selected_optionals)
    return result
