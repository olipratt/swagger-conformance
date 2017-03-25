"""
Functions for generating hypothesis strategies for swagger-defined models and
properties.
"""
import logging

import hypothesis.strategies as hy_st


log = logging.getLogger(__name__)


def hypothesize_base_parameter(base_parameter_template):
    """Generate hypothesis strategy for a single Parameter.
    :type parameter_template: templates.BaseParameterTemplate
    """
    log.debug("Hypothesizing a parameter")

    if base_parameter_template.type == 'array':
        elements = hypothesize_base_parameter(base_parameter_template.children)
        hypothesized_param = \
            base_parameter_template.value_template.hypothesize(elements)
    elif base_parameter_template.type == 'object':
        properties = {}
        for name, model in base_parameter_template.children.items():
            log.debug("Hypothesizing key: %r", name)
            properties[name] = hypothesize_base_parameter(model)
        hypothesized_param = \
            base_parameter_template.value_template.hypothesize(properties)
    else:
        hypothesized_param = \
            base_parameter_template.value_template.hypothesize()

    return hypothesized_param


def hypothesize_parameters(parameters):
    """Generate hypothesis fixed dictionary mapping of parameters.

    :param parameters: The dictionary of parameter templates to generate from.
    :type parameters: dict
    """
    hypothesis_mapping = {}

    for parameter_name, parameter_template in parameters.items():
        hypothesized_param = hypothesize_base_parameter(parameter_template)
        hypothesis_mapping[parameter_name] = hypothesized_param

    return hy_st.fixed_dictionaries(hypothesis_mapping)
