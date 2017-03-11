import logging

import hypothesis

from client import SwaggerClient
from templates import APITemplate
from strategies import hypothesize_parameters


log = logging.getLogger(__name__)


def main(schema_path):
    client = SwaggerClient(schema_path)
    api_template = APITemplate(client)
    log.debug("Expanded endpoints as: %r", api_template)

    for operation in api_template.iter_template_operations():
        strategy = hypothesize_parameters(operation.parameters)

        @hypothesis.settings(max_examples=1)
        @hypothesis.given(strategy)
        def single_operation_test(params):
            log.info("Testing with params: %r", params)
            result = client.request(operation, params)
            assert result.status < 500

        single_operation_test()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main('http://127.0.0.1:5000/api/schema')
