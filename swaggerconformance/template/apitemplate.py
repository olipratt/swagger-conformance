"""
Templates for key parts of a Swagger-defined API which can be used to generate
specific API requests adhering to the definition.
"""
import logging

from .operationtemplate import OperationTemplate


log = logging.getLogger(__name__)


class APITemplate:
    """Template for an entire Swagger API.
    :type client: client.SwaggerClient
    """

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
        """Mapping of the endpoints of this API to their operations.
        :rtype: dict
        """
        return self._expanded_paths

    def iter_template_operations(self):
        """All operations of the API across all endpoints.

        :yields: OperationTemplate
        """
        for endpoint in self.endpoints:
            log.debug("Testing endpoint: %r", endpoint)
            for operation_type in self.endpoints[endpoint]:
                log.debug("Testing operation type: %r", operation_type)
                operation = self.endpoints[endpoint][operation_type]
                log.info("Got operation: %r", operation)

                yield operation

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
