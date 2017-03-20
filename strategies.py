"""
Functions for generating hypothesis strategies for swagger-defined models and
properties.
"""
import logging

import hypothesis.strategies as hy_st

from templates import ParameterTemplate, ModelTemplate


log = logging.getLogger(__name__)


JSON_STRATEGY = hy_st.recursive(
    hy_st.floats() | hy_st.booleans() | hy_st.text() | hy_st.none(),
    lambda children: hy_st.dictionaries(hy_st.text(), children),
    max_leaves=5)

JSON_OBJECT_STRATEGY = hy_st.dictionaries(hy_st.text(), JSON_STRATEGY)


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


def hypothesize_parameters(parameters):
    """Generate hypothesis fixed dictionary mapping of parameters.

    :param parameters: The dictionary of parameter templates to generate from.
    :type parameters: dict
    """
    strategy_type_map = {'string': hy_st.text,
                         'integer': hy_st.integers,
                         'float': hy_st.floats}
    hypothesis_mapping = {}

    for parameter_name, parameter_template in parameters.items():
        if isinstance(parameter_template, ParameterTemplate):
            log.debug("Simple parameter strategy: %r", parameter_name)
            hypothesized_param = strategy_type_map[parameter_template.type]()
            hypothesis_mapping[parameter_name] = hypothesized_param
        else:
            log.debug("Model parameter strategy: %r", parameter_name)
            assert isinstance(parameter_template, ModelTemplate)
            hypothesized_model = hypothesize_model(parameter_template)
            hypothesis_mapping[parameter_name] = hypothesized_model

    return hy_st.fixed_dictionaries(hypothesis_mapping)
