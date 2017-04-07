"""
Main high-level entrypoints for validating swagger conformance.
"""
import logging

import hypothesis

from .client import SwaggerClient
from .template import APITemplate, ValueFactory


log = logging.getLogger(__name__)


def validate_schema(schema_path, num_tests_per_op=20):
    """Fully validate the API defined by the given schema.

    :param schema_path: The path to / URL of the schema to validate.
    :type schema_path: str
    :param num_tests_per_op: How many tests to run of each API operation.
    :type num_tests_per_op: int
    """
    client = SwaggerClient(schema_path)
    api_template = APITemplate(client)
    log.debug("Expanded endpoints as: %r", api_template)

    for operation in api_template.template_operations():
        validate_operation(client, operation, num_tests_per_op)


def validate_operation(client, operation, num_tests=20):
    """Fully validate the API operation using the provided client.

    :param client: The client to use to access the API.
    :type client: SwaggerClient
    :param operation: The operation to test.
    :type operation: template.operationtemplate.OperationTemplate
    :param num_tests: How many tests to run of each API operation.
    :type num_tests: int
    """
    log.info("Testing operation: %r", operation)
    strategy = operation.hypothesize_parameters(ValueFactory())

    @hypothesis.settings(max_examples=num_tests)
    @hypothesis.given(strategy)
    def single_operation_test(client, operation, params):
        """Test an operation fully.

        :param client: The client to use to access the API.
        :type client: SwaggerClient
        :param operation: The operation to test.
        :type operation: template.operationtemplate.OperationTemplate
        :param params: The dictionary of parameters to use on the operation.
        :type params: dict
        """
        log.info("Testing with params: %r", params)
        result = client.request(operation, params)
        assert result.status in operation.response_codes, \
            "{} not in {}".format(result.status, operation.response_codes)
        assert 'application/json' in result.header['Content-Type'], \
            "application/json not in {}".format(result.header['Content-Type'])

    # Run the test, which takes one less parameter than expected due to the
    # hypothesis decorator providing the last one.
    single_operation_test(client, operation) # pylint: disable=I0011,E1120
