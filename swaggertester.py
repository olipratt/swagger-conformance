import logging

import hypothesis
import hypothesis.strategies as hy_st

from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client
# pyswagger makes INFO level logs regularly by default, so lower its logging
# level to prevent the spam.
logging.getLogger("pyswagger").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


log = logging.getLogger(__name__)


JSON_STRATEGY = hy_st.recursive(
    hy_st.floats() | hy_st.booleans() | hy_st.text() | hy_st.none(),
    lambda children: hy_st.dictionaries(hy_st.text(), children),
    max_leaves=5)

JSON_OBJECT_STRATEGY = hy_st.dictionaries(hy_st.text(), JSON_STRATEGY)


class SwaggerClient:
    """Client to use to access the Swagger application."""

    def __init__(self, schema_path):
        self._schema_path = schema_path
        self._app = App.create(schema_path)

    def __repr__(self):
        return "{}(schema_path={})".format(self.__class__.__name__,
                                           self._schema_path)

    @property
    def app(self):
        return self._app

    def request(self, operation, parameters):
        """Perform a request.

        :param operation: The operation to perform.
        :type operation: OperationTemplate
        :param parameters: The parameters to use on the operation.
        :type parameters: dict
        """
        client = Client(Security(self._app))
        result = client.request(operation.operation(**parameters))

        return result


class ParameterTemplate:
    """Template for a parameter to pass to an operation on an endpoint."""

    def __init__(self, parameter):
        assert parameter.type is not None
        self._type = parameter.type
        assert parameter.name is not None
        self._name = parameter.name

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self._name,
                                             self._type)

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type


class ModelTemplate:
    """Template for a generic parameter, which may be one of many types,
    defining the model it follows.

    In the Swagger/OpenAPI world, this maps to a `Schema Object`.
    """

    def __init__(self, app, schema):
        self._app = app
        self._schema = schema
        self._contents = None

        self._build()

    @property
    def contents(self):
        return self._contents

    def _build(self):
        ref = getattr(self._schema, '$ref')
        log.debug("Ref is: %r", ref)
        if ref is not None:
            schema = self._app.resolve(ref)
        else:
            schema = self._schema
        log.debug("Schema: %r", schema)
        log.debug("Schema name: %r", schema.name)

        if schema.type == 'object':
            log.debug("Properties: %r", schema.properties)
            if len(schema.properties) > 0:
                self._contents = {}
                for prop_name in schema.properties:
                    log.debug("This prop: %r", prop_name)
                    child = ModelTemplate(self._app,
                                          schema.properties[prop_name])
                    self._contents[prop_name] = child

        else:
            log.warning("SKIPPING SCHEMA TYPE: %r - NOT IMPLEMENTED",
                        schema.type)


class OperationTemplate:
    """Template for an operation on an endpoint."""

    def __init__(self, app, operation):
        self._app = app
        self._operation = operation
        self._parameters = {}

        self._populate_parameters()

    def __repr__(self):
        return "{}(operation={}, params={})".format(self.__class__.__name__,
                                                    self._operation,
                                                    self._parameters)

    @property
    def operation(self):
        return self._operation

    @property
    def parameters(self):
        return self._parameters

    def _populate_parameters(self):
        for parameter in self._operation.parameters:
            log.debug("Handling parameter: %r", parameter.name)

            # Every parameter has a name. It's either a well defined parameter,
            # or it's the lone body parameter, in which case it's a Model
            # defined by a schema.
            if parameter.name == 'X-Fields':
                log.warning("SKIPPING X-Fields PARAM - NOT IMPLEMENTED")
            elif parameter.schema is None:
                log.debug("Fully defined parameter")
                param_template = ParameterTemplate(parameter)
                self._parameters[parameter.name] = param_template
            else:
                log.debug("Schema defined parameter")
                model_template = ModelTemplate(self._app, parameter.schema)
                self._parameters[parameter.name] = model_template


class EndpointCollection:

    operations = ["get", "put", "post", "delete"]

    def __init__(self, client):
        log.debug("Creating new endpoint collection for: %r", client)
        self._client = client
        self._app = client.app

        self._paths = self._app.root.paths.keys()
        log.debug("Found paths as: %s", self._paths)

        self._expanded_paths = {}
        for path in self._paths:
            self._expanded_paths[path] = self._expand_path(path)

    @property
    def endpoints(self):
        return self._expanded_paths

    def _expand_path(self, path):
        log.debug("Expanding path: %r", path)

        operations_map = {}
        for operation_name in self.operations:
            log.debug("Accessing operation: %s", operation_name)
            operation = getattr(self._app.root.paths[path], operation_name)
            if operation is not None:
                log.debug("Have operation")
                operations_map[operation_name] = OperationTemplate(self._app,
                                                                   operation)

        log.debug("Expanded path as: %r", operations_map)
        return operations_map


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

    assert False


def hypothesize_parameters(parameters):
    """Generate hypothesis fixed dictionary mapping of parameters.

    :param parameters: The dictionary of parameter templates to generate from.
    :type parameters: dict
    """
    strategy_type_map = {'string': hy_st.text}
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


def main(schema_path):
    client = SwaggerClient(schema_path)
    endpoints_clctn = EndpointCollection(client)
    log.debug("Expanded endpoints as: %r", endpoints_clctn)

    for endpoint in endpoints_clctn.endpoints:
        log.debug("Testing endpoint: %r", endpoint)
        for operation_type in endpoints_clctn.endpoints[endpoint]:
            log.debug("Testing operation type: %r", operation_type)
            operation = endpoints_clctn.endpoints[endpoint][operation_type]
            log.info("Got operation: %r", operation)

            strategy = hypothesize_parameters(operation.parameters)

            @hypothesis.given(strategy)
            def single_operation_test(params):
                log.info("Testing with params: %r", params)
                result = client.request(operation, params)
                assert result.status < 500

            single_operation_test()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main('http://127.0.0.1:5000/api/schema')
