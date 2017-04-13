import logging

from swaggerconformance import api_conformance_test


log = logging.getLogger(__name__)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    api_conformance_test('http://127.0.0.1:5000/api/schema')
