"""
Functions for generating hypothesis strategies for swagger-defined models and
properties.
"""
import logging

import hypothesis.strategies as hy_st


log = logging.getLogger(__name__)


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


def hypothesize_parameter(parameter_template):
    """Generate hypothesis strategy for a single Parameter.
    :type parameter_template: template.parametertemplate.ParameterTemplate
    """
    log.debug("Hypothesizing a parameter")

    if parameter_template.type == 'array':
        elements = hypothesize_parameter(parameter_template.items)
        hypothesized_param = \
            parameter_template.value_template.hypothesize(elements)
    elif parameter_template.type == 'object':
        properties = {}
        for name, model in parameter_template.properties.items():
            log.debug("Hypothesizing key: %r", name)
            properties[name] = hypothesize_parameter(model)
        hypothesized_param = \
            parameter_template.value_template.hypothesize(properties)
    else:
        hypothesized_param = parameter_template.value_template.hypothesize()

    return hypothesized_param


def hypothesize_parameters(parameters):
    """Generate hypothesis fixed dictionary mapping of parameters.

    :param parameters: The dictionary of parameter templates to generate from.
    :type parameters: dict
    """
    required_params = {}
    optional_params = {}

    for parameter_name, parameter_template in parameters.items():
        hypothesized_param = hypothesize_parameter(parameter_template)
        if parameter_template.required:
            required_params[parameter_name] = hypothesized_param
        else:
            optional_params[parameter_name] = hypothesized_param

    return combined_dicts_strategy(required_params, optional_params)
