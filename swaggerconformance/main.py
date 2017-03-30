import logging

import hypothesis

from .client import SwaggerClient
from .template import APITemplate
from .strategies import hypothesize_parameters


log = logging.getLogger(__name__)


def validate_schema(schema_path):
    """Fully validate the API defined by the given schema."""
    client = SwaggerClient(schema_path)
    api_template = APITemplate(client)
    log.debug("Expanded endpoints as: %r", api_template)

    for operation in api_template.template_operations():
        validate_operation(client, operation)


def validate_operation(client, operation):
    """Fully validate the API operation using the provided client."""
    strategy = hypothesize_parameters(operation.parameters)

    @hypothesis.settings(max_examples=20)
    @hypothesis.given(strategy)
    def single_operation_test(client, operation, params):
        """Test an operation fully.

        :param client: The client to use to access the API.
        :type client: SwaggerClient
        :param operation: The operation to test.
        :type operation: OperationTemplate
        :param params: The dictionary of parameters to use on the operation.
        :type params: dict
        """
        log.info("Testing with params: %r", params)
        result = client.request(operation, params)
        assert result.status in operation.response_codes, \
            "{} not in {}".format(result.status, operation.response_codes)
        assert 'application/json' in result.header['Content-Type'], \
            "application/json not in {}".format(result.header['Content-Type'])

    single_operation_test(client, operation)
