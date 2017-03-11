import logging

from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client
# pyswagger and requests make INFO level logs regularly by default, so lower
# their logging levels to prevent the spam.
logging.getLogger("pyswagger").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)


log = logging.getLogger(__name__)


class SwaggerClient:
    """Client to use to access the Swagger application."""

    def __init__(self, schema_path):
        """Create a new Swagger API client.

        :param schema_path: The URL of or file path to the API definition.
        :type schema_path: str
        """
        self._schema_path = schema_path
        self._app = App.create(schema_path)

    def __repr__(self):
        return "{}(schema_path={})".format(self.__class__.__name__,
                                           self._schema_path)

    @property
    def app(self):
        return self._app

    def request(self, operation, parameters):
        """Make a request against a certain operation on the API.

        :param operation: The operation to perform.
        :type operation: OperationTemplate
        :param parameters: The parameters to use on the operation.
        :type parameters: dict

        :rtype pyswagger.
        """
        client = Client(Security(self._app))
        result = client.request(operation.operation(**parameters))

        return result
