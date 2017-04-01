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
        result = parameter_template.value_template.hypothesize(elements)
    elif parameter_template.type == 'object':
        reqd_props = {name: hypothesize_parameter(model)
                      for name, model in parameter_template.properties.items()
                      if name in parameter_template.required_properties}
        opt_props = {name: hypothesize_parameter(model)
                     for name, model in parameter_template.properties.items()
                     if name not in parameter_template.required_properties}
        result = parameter_template.value_template.hypothesize(reqd_props,
                                                               opt_props)
    else:
        result = parameter_template.value_template.hypothesize()

    return result


def hypothesize_parameters(parameters):
    """Generate hypothesis fixed dictionary mapping of parameters.

    :param parameters: The dictionary of parameter templates to generate from.
    :type parameters: dict
    """
    required_params = {param_name: hypothesize_parameter(param_template)
                       for param_name, param_template in parameters.items()
                       if param_template.required}
    optional_params = {param_name: hypothesize_parameter(param_template)
                       for param_name, param_template in parameters.items()
                       if not param_template.required}

    return merge_optional_dict_strategy(required_params, optional_params)
