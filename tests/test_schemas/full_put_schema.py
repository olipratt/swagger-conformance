'''
A simple REST API exposing a swagger schema.
'''
import logging
import os.path

from flask import request
from flask_restplus import Resource, fields

from common import main, api


log = logging.getLogger(__name__)


example_ns = api.namespace('example', description="Example operations")


# Define some custom fields (actually just still swagger specified ones).
class ByteField(fields.String):
    __schema_format__ = 'byte'


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
    'b64bytes': ByteField(required=True,
                          description='Some bytes',
                          example="c3dhZ2dlcg=="),
    'b64bytesenum': ByteField(required=True,
                              description='Some bytes',
                              enum=['QQ==', 'Qg==', 'Qw==', 'RA=='],
                              example="QQ=="),
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


if __name__ == '__main__':
    main(os.path.splitext(os.path.basename(__file__))[0] + '.json')
