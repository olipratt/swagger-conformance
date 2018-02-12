"""
Templates for key parts of a Swagger-defined API which can be used to generate
specific API requests adhering to the definition.
"""
import logging

from ._operation import Operation

__all__ = ["Api"]


log = logging.getLogger(__name__)


class Api:
    """Template for an entire Swagger API.

    :type client: client.Client
    """

    _OPERATIONS = ["get", "put", "post", "delete"]

    def __init__(self, client):
        log.debug("Creating new endpoint collection for: %r", client)
        self._client = client
        self._app = client._pyswagger_app  # pylint: disable=protected-access

        self._endpoints_map = {path: self._method_to_op_map(path)
                               for path in self._app.root.paths}

    @property
    def endpoints(self):
        """Mapping of the endpoints of this API to their operations.

        :rtype: dict(str, dict(str, schema.Operation))
        """
        return self._endpoints_map

    def operation(self, operation_id):
        """Access a single operation by its unique operation ID.

        :rtype: schema.Operation
        """
        # Defer to the underlying pyswagger library to do the lookup.
        raw_op = self._app.op[operation_id]
        return self.endpoints[raw_op.path][raw_op.method]

    def operations(self):
        """All operations of the API across all endpoints.

        :rtype: Generator(schema.Operation)
        """
        return (self.endpoints[endpoint][operation_type]
                for endpoint in self.endpoints
                for operation_type in self.endpoints[endpoint])

    def _method_to_op_map(self, path):
        log.debug("Expanding path: %r", path)
        operations_defs = self._app.root.paths[path]

        operations_map = {}
        for operation_name in self._OPERATIONS:
            log.debug("Accessing operation: %s", operation_name)
            operation = getattr(operations_defs, operation_name)
            if operation is not None:
                log.debug("Have operation")
                operations_map[operation_name] = Operation(operation)

        log.debug("Expanded path as: %r", operations_map)
        return operations_map
