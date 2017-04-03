import logging
import os.path

from flask import request
from flask_restplus import Resource, fields

from common import api, main


log = logging.getLogger(__name__)


# This collects the API operations into named groups under a root URL.
example_ns = api.namespace('example', description="Example operations")


# Specifications of the objects accepted/returned by the API.
ExampleObj = api.model('Example', {
    'intinclimits': fields.Integer(required=True,
                                   description='integer inc limits',
                                   max=3,
                                   min=0,
                                   exclusiveMax=False,
                                   exclusiveMin=False,
                                   example=1),
    'intexclimits': fields.Integer(required=True,
                                   description='integer inc limits',
                                   max=3,
                                   min=0,
                                   exclusiveMax=True,
                                   exclusiveMin=True,
                                   example=1),
    'imulinclimits': fields.Integer(required=True,
                                    description='multiple integer inc limits',
                                    max=10,
                                    min=0,
                                    exclusiveMax=False,
                                    exclusiveMin=False,
                                    multiple=2,
                                    example=8),
    'imulexclimits': fields.Integer(required=True,
                                    description='multiple integer exc limits',
                                    max=10,
                                    min=0,
                                    exclusiveMax=True,
                                    exclusiveMin=True,
                                    multiple=2,
                                    example=8),
    'imulofflimits': fields.Integer(required=True,
                                    description='multiple integer off limits',
                                    max=9,
                                    min=1,
                                    exclusiveMax=False,
                                    exclusiveMin=False,
                                    multiple=2,
                                    example=8),
    'imulonlimits': fields.Integer(required=True,
                                   description='multiple integer on limits',
                                   max=9,
                                   min=1,
                                   exclusiveMax=True,
                                   exclusiveMin=True,
                                   multiple=2,
                                   example=8),
    'fltinclimits': fields.Float(required=True,
                                 description='float inc limits',
                                 max=3.0,
                                 min=0.0,
                                 exclusiveMax=False,
                                 exclusiveMin=False,
                                 example=1.0),
    'fltexclimits': fields.Float(required=True,
                                 description='float inc limits',
                                 max=3.0,
                                 min=0.0,
                                 exclusiveMax=True,
                                 exclusiveMin=True,
                                 example=1.0),
    'fmulinclimits': fields.Float(required=True,
                                  description='multiple float inc limits',
                                  max=3.0,
                                  min=0.0,
                                  exclusiveMax=False,
                                  exclusiveMin=False,
                                  multiple=1.5,
                                  example=1.5),
    'fmulexclimits': fields.Float(required=True,
                                  description='multiple float exc limits',
                                  max=3.0,
                                  min=0.0,
                                  exclusiveMax=True,
                                  exclusiveMin=True,
                                  multiple=1.5,
                                  example=1.5),
    'fmulofflimits': fields.Float(required=True,
                                  description='multiple float off limits',
                                  max=4.0,
                                  min=1.0,
                                  exclusiveMax=False,
                                  exclusiveMin=True,
                                  multiple=1.5,
                                  example=1.5),
    'strlen': fields.String(required=True,
                            description='length limited str',
                            max_length=4,
                            min_length=2,
                            example="exs"),
    'listlen': fields.List(fields.String,
                           required=True,
                           description='length limited list',
                           max_length=4,
                           min_length=2,
                           example=["some", "strings", "here"]),
})


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
