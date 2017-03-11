import logging

from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client
# pyswagger makes INFO level logs regularly by default, so lower its logging
# level to prevent the spam.
logging.getLogger("pyswagger").setLevel(logging.WARNING)


log = logging.getLogger(__name__)


class ParameterTemplate:

    def __init__(self, parameter):
        assert parameter.type is not None
        self._type = parameter.type
        assert parameter.name is not None
        self._name = parameter.name

    def __repr__(self):
        return "ParameterTemplate(name={}, type={})".format(self._name,
                                                            self._type)


class EndpointCollection:

    operations = ["get", "put"]

    def __init__(self, schema_path):
        log.debug("Creating new endpoint collection for: %r", schema_path)
        self._schema_path = schema_path

        self._app = App.create(schema_path)

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
            operation_params = {}
            operation = getattr(self._app.root.paths[path], operation_name)
            if operation is not None:
                log.debug("Have operation")
                operations_map[operation_name] = operation_params
                for parameter in operation.parameters:
                    log.debug("Handling parameter: %r", parameter.name)

                    if parameter.schema is None:
                        log.debug("Fully defined parameter")
                        param_template = ParameterTemplate(parameter)
                        operation_params[parameter.name] = param_template
                    else:
                        log.debug("Schema defined parameter")
                        log.warning("SKIPPING SCHEMA PARAM - NOT IMPLEMENTED")

        log.debug("Expanded path as: %r", operations_map)
        return operations_map


def main(schema_path):
    endpoints = EndpointCollection(schema_path)
    log.debug("Expanded endpoints as: %r", endpoints)

    operation = endpoints.endpoints['/apps/{appid}']['get']



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main('http://127.0.0.1:5000/api/schema')
