import logging
import os.path

from flask import request
from flask_restplus import Resource, fields

from common import api, main


log = logging.getLogger(__name__)


# This collects the API operations into named groups under a root URL.
example_ns = api.namespace('example', description="Example operations")

ExampleObj = api.model('Example', {
    'in_str': fields.String(required=True,
                            description='your str',
                            example="exs"),
})

@example_ns.route('/<string:in_str>')
class ExampleResource(Resource):

    @api.marshal_with(ExampleObj)
    def get(self, in_str):
        """Takes in data"""
        log.debug("Got parameter: %r", in_str)
        log.debug("Got body: %r", request.data)
        return {"in_str": in_str}


if __name__ == '__main__':
    main(os.path.splitext(os.path.basename(__file__))[0] + '.json')
