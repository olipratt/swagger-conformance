'''
A simple REST API exposing a swagger schema.
'''
import logging
import os.path
import random

from flask import request
from flask_restplus import Resource, fields

from common import main, api


log = logging.getLogger(__name__)


example_ns = api.namespace('example', description="Example operations")


class Colour:
    def __init__(self, value):
        if isinstance(value, str):
            self._int_value = int(value.lstrip('#'), base=16)
        elif isinstance(value, int):
            self._int_value = value
        else:
            raise AssertionError("Invalid Type")

    @property
    def int(self):
        return self._int_value

    @property
    def hex(self):
        return "#{0:06x}".format(self._int_value)


class HexColourField(fields.String):
    __schema_format__ = "hexcolour"


class IntColourField(fields.Integer):
    __schema_format__ = "intcolour"


# Specifications of the objects accepted/returned by the API.
IdModel = api.model('IdModel', {
    'id': fields.Integer(required=True,
                         description='Id number',
                         example=123456),
})
HexColourModel = api.model('HexColourModel', {
    'hexcolour': HexColourField(required=True,
                                description='Hex colour',
                                example="#123456",
                                min_length=7,
                                max_length=7),
})

IntColourModel = api.model('IntColourModel', {
    'intcolour': IntColourField(required=True,
                                description='Int colour',
                                example=16777215,
                                min=0,
                                max=16777215),
})

DATA_DICT = {}

@example_ns.route('')
class ExampleCollection(Resource):
    """Resource allowing access to different types of methods and models."""

    @api.marshal_with(IdModel)
    def post(self):
        """Return a new ID."""
        new_id = random.randint(0, 0xffffffff)
        DATA_DICT[new_id] = None
        return {'id': new_id}


@example_ns.route('/<int:int_id>/hexcolour')
class HexColourResource(Resource):

    @api.marshal_with(HexColourModel)
    def get(self, int_id):
        """Return the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        return {'hexcolour': DATA_DICT[int_id].hex}

    @api.expect(HexColourModel)
    @api.response(204, 'Colour successfully updated.')
    def put(self, int_id):
        """Set the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        log.debug("Got body: %r", request.data)
        DATA_DICT[int_id] = Colour(request.json['hexcolour'])
        return None, 204


@example_ns.route('/<int:int_id>/intcolour')
class IntColourResource(Resource):

    @api.marshal_with(IntColourModel)
    def get(self, int_id):
        """Return the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        return {'intcolour': DATA_DICT[int_id].int}

    @api.expect(IntColourModel)
    @api.response(204, 'Colour successfully updated.')
    def put(self, int_id):
        """Set the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        log.debug("Got body: %r", request.data)
        DATA_DICT[int_id] = Colour(request.json['intcolour'])
        return None, 204


if __name__ == '__main__':
    main(os.path.splitext(os.path.basename(__file__))[0] + '.json')
