'''
A simple REST API exposing a swagger schema.
'''
import logging
import sys
import os.path
import json

from flask import Flask, request
from werkzeug.routing import IntegerConverter
from flask_restplus import Resource, Api, fields


log = logging.getLogger(__name__)
app = Flask(__name__)


# By default Flask doesn't handle negative integer path parameters - fix that.
class IntsIncNegConverter(IntegerConverter):
    regex = r'-?' + IntegerConverter.regex
app.url_map.converters['int'] = IntsIncNegConverter

# Globally enable input validation.
app.config['RESTPLUS_VALIDATE'] = True

# Use a non-empty 'prefix' (becomes swagger 'basePath') for interop reasons -
# if it's empty then the basePath is '/', which with an API enpoint appended
# becomes '//<endpoint>' (because they are always prefixed themselves with a
# '/') and that is not equivalent to '/<endpoint'.
API_URL_PREFIX = '/api'
api = Api(app,
          version='1.0',
          title='Example API',
          description='A test REST API',
          prefix=API_URL_PREFIX,
          catch_all_404s=True)

# This collects the API operations into named groups under a root URL.
schema_ns = api.namespace('schema', description="This API's schema operations")


@schema_ns.route('', doc=False)
class SchemaResource(Resource):
    """Resource allowing access to the OpenAPI schema for the entire API."""

    def get(self):
        """Return the OpenAPI schema."""
        schema = api.__schema__
        return schema


def _dump_schema(output_file_path):
    """Dump the API swagger schema to a file of the same name but suffix .json.
    """
    app.config['TESTING'] = True
    test_app = app.test_client()
    schema = json.loads(test_app.get(API_URL_PREFIX + '/schema').data.decode())
    schema["host"] = "127.0.0.1:5000"
    schema["schemes"] = ["http"]
    with open(output_file_path, 'w') as file_handle:
        # Write the file pretty-printed for readability, and with sorted keys
        # for minimal version control changes when regenerated.
        json.dump(schema, file_handle, indent=4, sort_keys=True)


def main(output_file_path):
    """Serve the API, or write the API schema to file if -w is provided."""
    # If run with -w, just write the schema to a .json file with the same name.
    if len(sys.argv) > 1 and sys.argv[1] == "-w":
        _dump_schema(output_file_path)
        sys.exit()

    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
    app.run()
