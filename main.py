import logging

from swaggerconformance import validate_schema


log = logging.getLogger(__name__)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    validate_schema('http://127.0.0.1:5000/api/schema')
