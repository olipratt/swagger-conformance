"""
Main high-level entrypoints for validating swagger conformance.
"""
import logging
import traceback

import hypothesis

from .client import Client
from .strategies import StrategyFactory

__all__ = ["api_conformance_test", "operation_conformance_test"]


log = logging.getLogger(__name__)


def api_conformance_test(schema_path, num_tests_per_op=20, cont_on_err=True):
    """Basic test of the conformance of the API defined by the given schema.

    :param schema_path: The path to / URL of the schema to validate.
    :type schema_path: str
    :param num_tests_per_op: How many tests to run of each API operation.
    :type num_tests_per_op: int
    :param cont_on_err: Validate all operations, or drop out on first error.
    :type cont_on_err: bool
    """
    client = Client(schema_path)
    log.debug("Expanded endpoints as: %r", client.api)

    hit_errors = []
    for operation in client.api.operations():
        try:
            operation_conformance_test(client, operation, num_tests_per_op)
        except Exception as e:
            log.exception("Validation falied of operation: %r", operation)
            hit_errors.append(traceback.format_exc())
            if not cont_on_err:
                raise

    if len(hit_errors) > 0:
        raise Exception("{} operation(s) failed conformance tests - check "
                        "output in logging and tracebacks below for "
                        "details\n{}".format(len(hit_errors),
                                             '\n'.join(hit_errors)))


def operation_conformance_test(client, operation, num_tests=20):
    """Test the conformance of the given operation using the provided client.

    :param client: The client to use to access the API.
    :type client: client.Client
    :param operation: The operation to test.
    :type operation: schema.Operation
    :param num_tests: How many tests to run of each API operation.
    :type num_tests: int
    """
    log.info("Testing operation: %r", operation)
    strategy = operation.parameters_strategy(StrategyFactory())

    @hypothesis.settings(
        max_examples=num_tests,
        suppress_health_check=[hypothesis.HealthCheck.too_slow])
    @hypothesis.given(strategy)
    def single_operation_test(client, operation, params):
        """Test an operation fully.

        :param client: The client to use to access the API.
        :type client: client.Client
        :param operation: The operation to test.
        :type operation: schema.Operation
        :param params: The dictionary of parameters to use on the operation.
        :type params: dict
        """
        log.info("Testing with params: %r", params)
        result = client.request(operation, params)
        assert result.status in operation.response_codes, \
            "Response code {} not in {}".format(result.status,
                                                operation.response_codes)
        assert 'application/json' in result.headers['Content-Type'], \
            "application/json not in {}".format(result.headers['Content-Type'])

    # Run the test, which takes one less parameter than expected due to the
    # hypothesis decorator providing the last one.
    single_operation_test(client, operation) # pylint: disable=E1120
