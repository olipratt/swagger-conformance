"""
Functions for generating hypothesis strategies for swagger-defined models and
properties.
"""
import logging
import datetime
import io

import hypothesis.strategies as hy_st

from templates import ParameterTemplate, ModelTemplate


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


def hypothesize_model(model_template):
    """Generate hypothesis strategies for a model.

    :param model_template: The model template to prepare a strategy for.
    :type model_template: ModelTemplate
    """
    log.debug("Hypothesizing a model")
    created_model = None

    if model_template.type == 'object':
        if model_template.children is None:
            log.debug("Model is arbitrary object")
            created_model = JSON_OBJECT_STRATEGY
        else:
            log.debug("Model is object with specified keys")
            model_dict = {}
            for name, model in model_template.children.items():
                log.debug("Hypothesizing key: %r", name)
                model_dict[name] = hypothesize_model(model)
            created_model = hy_st.fixed_dictionaries(model_dict)
    elif model_template.type == 'integer':
        created_model = hy_st.integers()
    elif model_template.type == 'string':
        if model_template.enum is not None:
            created_model = hy_st.sampled_from(model_template.enum)
        elif model_template.format == 'date':
            created_model = DATE_STRATEGY
        elif model_template.format == 'date-time':
            created_model = DATETIME_STRATEGY
        else:
            created_model = hy_st.text()
    elif model_template.type == 'number':
        created_model = hy_st.floats()
    elif model_template.type == 'boolean':
        created_model = hy_st.booleans()
    elif model_template.type == 'array':
        created_model = hy_st.lists(hypothesize_model(model_template.children))

    assert created_model is not None, \
        "Unrecognised model type: {}".format(model_template.type)

    return created_model


def hypothesize_parameter(parameter_template):
    """Generate hypothesis strategy for a single Parameter.
    :type parameter_template: ParameterTemplate
    """
    if parameter_template.type == 'array':
        elements = hypothesize_parameter(parameter_template.children)
        hypothesized_param = \
            parameter_template.value_template.hypothesize(elements)
    else:
        hypothesized_param = parameter_template.value_template.hypothesize()

    # if parameter_template.type == 'array':
    #     hypothesized_param = \
    #         hy_st.lists(hypothesize_parameter(parameter_template.children))
    # elif parameter_template.type == 'string':
    #     if parameter_template.enum is not None:
    #         hypothesized_param = hy_st.sampled_from(parameter_template.enum)
    #     elif parameter_template.format == 'date':
    #         hypothesized_param = DATE_STRATEGY
    #     elif parameter_template.format == 'date-time':
    #         hypothesized_param = DATETIME_STRATEGY
    #     else:
    #         if parameter_template.is_path:
    #             hypothesized_param = hy_st.text(min_size=1)
    #         elif parameter_template.is_header:
    #             hypothesized_param = hy_st.text(
    #                 alphabet=CHARS_NO_RETURN_STRATEGY).map(str.lstrip)
    #         else:
    #             hypothesized_param = hy_st.text()
    # elif parameter_template.type == 'integer':
    #     hypothesized_param = hy_st.integers()
    # elif parameter_template.type == 'number':
    #     hypothesized_param = hy_st.floats()
    # elif parameter_template.type == 'file':
    #     hypothesized_param = FILE_STRATEGY

    assert hypothesized_param is not None, \
        "Unrecognised parameter type: {}".format(parameter_template.type)

    return hypothesized_param


def hypothesize_parameters(parameters):
    """Generate hypothesis fixed dictionary mapping of parameters.

    :param parameters: The dictionary of parameter templates to generate from.
    :type parameters: dict
    """
    hypothesis_mapping = {}

    for parameter_name, parameter_template in parameters.items():
        if isinstance(parameter_template, ParameterTemplate):
            log.debug("Simple parameter strategy: %r", parameter_name)
            hypothesized_param = hypothesize_parameter(parameter_template)
            hypothesis_mapping[parameter_name] = hypothesized_param
        else:
            log.debug("Model parameter strategy: %r", parameter_name)
            assert isinstance(parameter_template, ModelTemplate)
            hypothesized_model = hypothesize_model(parameter_template)
            hypothesis_mapping[parameter_name] = hypothesized_model

    return hy_st.fixed_dictionaries(hypothesis_mapping)
