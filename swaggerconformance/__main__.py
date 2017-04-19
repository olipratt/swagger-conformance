"""
Allow running the package from the command line directly with:

``python -m swaggerconformance <url-or-path-to-schema> [-n num-tests-per-op]``

to run the basic conformance test of the API defined by the given schema.
"""
import sys
import argparse

from swaggerconformance import api_conformance_test


def main(raw_args):
    """Run a basic API conformance test with the supplied command line args."""
    parser = argparse.ArgumentParser(
        prog='python -m swaggerconformance',
        description='Basic Swagger-defined API conformance test.')
    parser.add_argument('schema_path', help='URL or path to Swagger schema')
    parser.add_argument('-n', dest='num_tests_per_op', metavar='N', type=int,
                        default=20,
                        help="number of tests to run per API operation")
    parsed_args = parser.parse_args(raw_args)
    api_conformance_test(parsed_args.schema_path,
                         num_tests_per_op=parsed_args.num_tests_per_op)


if __name__ == "__main__":
    main(sys.argv)  # pragma: no cover - We import this module to test it
