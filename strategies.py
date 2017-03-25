"""
Functions for generating hypothesis strategies for swagger-defined models and
properties.
"""
import logging

import hypothesis.strategies as hy_st

from templates import ParameterTemplate, ModelTemplate


log = logging.getLogger(__name__)


def hypothesize_model(model_template):
    """Generate hypothesis strategies for a model.

    :param model_template: The model template to prepare a strategy for.
    :type model_template: ModelTemplate
    """
    log.debug("Hypothesizing a model")

    if model_template.type == 'array':
        elements = hypothesize_model(model_template.children)
        created_model = model_template.value_template.hypothesize(elements)
    elif model_template.type == 'object':
        properties = {}
        for name, model in model_template.children.items():
            log.debug("Hypothesizing key: %r", name)
            properties[name] = hypothesize_model(model)
        created_model = model_template.value_template.hypothesize(properties)
    else:
        created_model = model_template.value_template.hypothesize()

    return created_model


def hypothesize_parameter(parameter_template):
    """Generate hypothesis strategy for a single Parameter.
    :type parameter_template: ParameterTemplate
    """
    log.debug("Hypothesizing a parameter")

    if parameter_template.type == 'array':
        elements = hypothesize_parameter(parameter_template.children)
        hypothesized_param = \
            parameter_template.value_template.hypothesize(elements)
    else:
        hypothesized_param = parameter_template.value_template.hypothesize()

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
