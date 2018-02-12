"""
A client for accessing a remote swagger-defined API.
"""
import logging

from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client as PyswaggerClient

from .codec import CodecFactory
from .schema import Api
from .response import Response

# pyswagger and requests make INFO level logs regularly by default, so lower
# their logging levels to prevent the spam.
logging.getLogger("pyswagger").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

__all__ = ["Client"]


log = logging.getLogger(__name__)


class Client:
    """Client to use to access the Swagger application according to its schema.

    :param schema_path: The URL of or file path to the API definition.
    :type schema_path: str
    :param codec: Used to convert between JSON and objects.
    :type codec: codec.CodecFactory or None
    """

    def __init__(self, schema_path, codec=None):
        self._schema_path = schema_path

        if codec is None:
            codec = CodecFactory()

        self._prim_factory = \
            codec._pyswagger_factory  # pylint: disable=protected-access

        self._app = App.load(schema_path, prim=self._prim_factory)
        self._app.prepare()

        self._api = Api(self)

    def __repr__(self):
        return "{}(schema_path={!r})".format(self.__class__.__name__,
                                             self._schema_path)

    @property
    def api(self):
        """The API accessible from this client.

        :rtype: `schema.Api`
        """
        return self._api

    def request(self, operation, parameters):
        """Make a request against a certain operation on the API.

        :param operation: The operation to perform.
        :type operation: schema.Operation
        :param parameters: The parameters to use on the operation.
        :type parameters: dict

        :rtype: pyswagger.io.Response
        """
        client = PyswaggerClient(Security(self._app))
        result = client.request(operation._pyswagger_operation(**parameters))  # pylint: disable=protected-access

        return Response(result)

    @property
    def _pyswagger_app(self):
        """The underlying pyswagger definition of the app - useful elsewhere
        internally but not expected to be referenced external to the package.

        :rtype: pyswagger.core.App
        """
        return self._app
