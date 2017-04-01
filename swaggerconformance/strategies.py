"""
Functions for generating hypothesis strategies for swagger-defined models and
properties.
"""
import logging

from .template.strategies import merge_optional_dict_strategy


log = logging.getLogger(__name__)


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
        required_properties = {}
        optional_properties = {}
        for name, model in parameter_template.properties.items():
            log.debug("Hypothesizing key: %r", name)
            if name in parameter_template.required_properties:
                required_properties[name] = hypothesize_parameter(model)
            else:
                optional_properties[name] = hypothesize_parameter(model)
        hypothesized_param = \
            parameter_template.value_template.hypothesize(required_properties,
                                                          optional_properties)
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

    return merge_optional_dict_strategy(required_params, optional_params)
