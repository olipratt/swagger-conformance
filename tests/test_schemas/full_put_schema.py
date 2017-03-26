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
example_ns = api.namespace('example', description="Example operations")


# Specifications of the objects accepted/returned by the API.
ExampleObj = api.model('Example', {
    'raw': fields.Raw(required=True,
                      description='Raw data',
                      example={"any_data": "you_like_goes_here"}),
    'whole': fields.Integer(required=True,
                            description='number data',
                            example=1234),
    'real': fields.Float(required=True,
                         description='real data',
                         example=123.456),
    'data': fields.String(required=True,
                          description='String data',
                          example="Some string"),
    'enumeration': fields.String(required=True,
                                 description='Specific string from enum',
                                 enum=['A', 'B', 'C', 'D'],
                                 example='C'),
    'truthy': fields.Boolean(required=True,
                             description='Bool data',
                             example=True),
    'list': fields.List(fields.String,
                        required=True,
                        description='List data',
                        example=["some", "strings", "here"]),
    'isod': fields.Date(required=True,
                        description='ISO date',
                        example='1990-12-31'),
    'isodt': fields.DateTime(required=True,
                             description='ISO datetime',
                             example='1985-04-12T23:20:50.52Z'),
})

@example_ns.route('')
class ExampleCollection(Resource):
    """Resource allowing access to different types of methods and models."""

    def get(self):
        """Return a string."""
        return "Hi"

    @api.response(204, 'Successful delete.')
    def delete(self):
        """Just return"""
        return None, 204


@example_ns.route('/<int:exint>')
class ExampleResource(Resource):

    @api.expect(ExampleObj)
    @api.response(204, 'App successfully updated.')
    def put(self, exint):
        """Takes in data"""
        log.debug("Got parameter: %r", exint)
        log.debug("Got body: %r", request.data)
        return None, 204


@schema_ns.route('')
class SchemaResource(Resource):
    """Resource allowing access to the OpenAPI schema for the entire API."""

    def get(self):
        """Return the OpenAPI schema."""
        schema = api.__schema__
        return schema


def _dump_schema():
    """Dump the API swagger schema to a file of the same name but suffix .json.
    """
    app.config['TESTING'] = True
    test_app = app.test_client()
    schema = json.loads(test_app.get(API_URL_PREFIX + '/schema').data.decode())
    schema["host"] = "127.0.0.1:5000"
    schema["schemes"] = ["http"]
    filename = os.path.splitext(os.path.basename(__file__))[0] + '.json'
    with open(filename, 'w') as file_handle:
        # Write the file pretty-printed for readability, and with sorted keys
        # for minimal version control changes when regenerated.
        json.dump(schema, file_handle, indent=4, sort_keys=True)


if __name__ == '__main__':
    # If run with -w, just write the schema to a .json file with the same name.
    if len(sys.argv) > 1 and sys.argv[1] == "-w":
        _dump_schema()
        sys.exit()

    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)
    app.run()
