import logging

import hypothesis.strategies as hy_st

from templates import (ParameterTemplate, ModelTemplate,
                       IntegerTemplate, StringTemplate, FloatTemplate,
                       BoolTemplate)


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
    contents = model_template.contents
    if contents is None:
        log.debug("Model is arbitrary object")
        return JSON_OBJECT_STRATEGY

    if isinstance(contents, dict):
        log.debug("Model is object with specified keys")
        model_dict = {}
        for name, model in contents.items():
            log.debug("Hypothesizing key: %r", name)
            model_dict[name] = hypothesize_model(model)
        return hy_st.fixed_dictionaries(model_dict)
    elif isinstance(contents, IntegerTemplate):
        return hy_st.integers()
    elif isinstance(contents, StringTemplate):
        return hy_st.text()
    elif isinstance(contents, FloatTemplate):
        return hy_st.floats()
    elif isinstance(contents, BoolTemplate):
        return hy_st.booleans()

    assert False


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
