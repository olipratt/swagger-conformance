"""
A client for accessing a remote swagger-defined API.
"""
import logging

from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client

from .codec import SwaggerCodec
from .apitemplates import APITemplate

# pyswagger and requests make INFO level logs regularly by default, so lower
# their logging levels to prevent the spam.
logging.getLogger("pyswagger").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

__all__ = ["SwaggerClient"]


log = logging.getLogger(__name__)


class SwaggerClient:
    """Client to use to access the Swagger application according to its schema.

    :param schema_path: The URL of or file path to the API definition.
    :type schema_path: str
    :param codec: Used to convert between JSON and objects.
    :type codec: codec.SwaggerCodec
    """

    def __init__(self, schema_path, codec=None):
        """Create a new Swagger API client."""
        self._schema_path = schema_path

        if codec is None:
            codec = SwaggerCodec()

        self._prim_factory = codec._swagger_factory

        self._app = App.load(schema_path, prim=self._prim_factory)
        self._app.prepare()

        self._api = APITemplate(self)

    def __repr__(self):
        return "{}(schema_path={!r})".format(self.__class__.__name__,
                                             self._schema_path)

    @property
    def app(self):
        """The App representing the API of the server.

        :rtype: pyswagger.core.App
        """
        return self._app

    @property
    def api(self):
        """The API accessible from this client.

        :rtype: `APITemplate`
        """
        return self._api

    def request(self, operation, parameters):
        """Make a request against a certain operation on the API.

        :param operation: The operation to perform.
        :type operation: apitemplates.OperationTemplate
        :param parameters: The parameters to use on the operation.
        :type parameters: dict

        :rtype: pyswagger.io.Response
        """
        client = Client(Security(self._app))
        result = client.request(operation.operation(**parameters))

        return result
