import logging

import hypothesis

from client import SwaggerClient
from templates import APITemplate
from strategies import hypothesize_parameters


log = logging.getLogger(__name__)


def validate_schema(schema_path):
    client = SwaggerClient(schema_path)
    api_template = APITemplate(client)
    log.debug("Expanded endpoints as: %r", api_template)

    for operation in api_template.iter_template_operations():
        validate_operation(client, operation)


def validate_operation(client, operation):
    strategy = hypothesize_parameters(operation.parameters)

    @hypothesis.settings(max_examples=20, suppress_health_check=[hypothesis.HealthCheck.too_slow])
    @hypothesis.given(strategy)
    def single_operation_test(client, params):
        log.info("Testing with params: %r", params)
        result = client.request(operation, params)
        assert result.status in operation.response_codes, \
            "{} not in {}".format(result.status, operation.response_codes)

    single_operation_test(client)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    validate_schema('http://127.0.0.1:5000/api/schema')
