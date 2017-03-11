import logging

import hypothesis

from client import SwaggerClient
from templates import OperationTemplate
from strategies import hypothesize_parameters


log = logging.getLogger(__name__)


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
