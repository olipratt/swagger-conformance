'''
A simple REST API exposing a swagger schema.
'''
import logging
import os.path
import random

from flask import request
from flask_restplus import Resource, fields, Model

from common import main, api


log = logging.getLogger(__name__)


example_ns = api.namespace('example', description="Example operations")
scene_ns = api.namespace('scenes', description="Scene operations")


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

class SceneModelClass(Model):
    @property
    def __schema__(self):
        schema = super().__schema__
        schema.update({"format": "scene"})
        return schema

SceneModel = SceneModelClass('Scene', {
    'foreground colour': IntColourField(required=True,
                                        description='Int colour',
                                        example=16777215,
                                        min=0,
                                        max=16777215),
    'background colour': IntColourField(required=True,
                                        description='Int colour',
                                        example=16777215,
                                        min=0,
                                        max=16777215)
})
api.add_model(SceneModel.name, SceneModel)

COLOUR_DATA_DICT = {}
SCENE_DATA_DICT = {}


@example_ns.route('')
class ExampleCollection(Resource):
    """Resource allowing access to different types of methods and models."""

    @api.marshal_with(IdModel)
    def post(self):
        """Return a new ID."""
        new_id = random.randint(0, 0xffffffff)
        COLOUR_DATA_DICT[new_id] = None
        return {'id': new_id}


@example_ns.route('/<int:int_id>/hexcolour')
class HexColourResource(Resource):

    @api.marshal_with(HexColourModel)
    def get(self, int_id):
        """Return the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        return {'hexcolour': COLOUR_DATA_DICT[int_id].hex}

    @api.expect(HexColourModel)
    @api.response(204, 'Colour successfully updated.')
    def put(self, int_id):
        """Set the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        log.debug("Got body: %r", request.data)
        COLOUR_DATA_DICT[int_id] = Colour(request.json['hexcolour'])
        return None, 204


@example_ns.route('/<int:int_id>/intcolour')
class IntColourResource(Resource):

    @api.marshal_with(IntColourModel)
    def get(self, int_id):
        """Return the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        return {'intcolour': COLOUR_DATA_DICT[int_id].int}

    @api.expect(IntColourModel)
    @api.response(204, 'Colour successfully updated.')
    def put(self, int_id):
        """Set the colour for the ID"""
        log.debug("Got parameter: %r", int_id)
        log.debug("Got body: %r", request.data)
        COLOUR_DATA_DICT[int_id] = Colour(request.json['intcolour'])
        return None, 204


@scene_ns.route('/<int:int_id>')
class SceneResource(Resource):

    @api.marshal_with(SceneModel)
    @api.response(404, "Scene doesn't exist.")
    def get(self, int_id):
        """Return the scene for the ID"""
        log.debug("Got parameter: %r", int_id)
        if int_id not in SCENE_DATA_DICT:
            api.abort(404, "Scene '{}' doesn't exist".format(int_id))
        return {'foreground colour': SCENE_DATA_DICT[int_id][0],
                'background colour': SCENE_DATA_DICT[int_id][1]}

    @api.expect(SceneModel)
    @api.response(204, 'Scene successfully updated.')
    def put(self, int_id):
        """Set the scene for the ID"""
        log.debug("Got parameter: %r", int_id)
        log.debug("Got body: %r", request.data)
        SCENE_DATA_DICT[int_id] = (request.json['foreground colour'],
                                   request.json['background colour'])
        return None, 204


if __name__ == '__main__':
    main(os.path.splitext(os.path.basename(__file__))[0] + '.json')
