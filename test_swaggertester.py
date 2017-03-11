import logging
import unittest

import swaggertester

TEST_SCHEMA_PATH = 'test_schema.json'
# SCHEMA_URL_BASE = 'http://127.0.0.1:5000/api'
# CONTENT_TYPE_JSON = 'application/json'


class EndpointCollectionTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        # No teardown of test fixtures required.
        pass

    def test_schema_parse(self):
        endpoints = swaggertester.EndpointCollection(TEST_SCHEMA_PATH)
        expected_endpoints = {'/schema', '/apps', '/apps/{appid}'}
        self.assertSetEqual(set(endpoints.endpoints.keys()),
                            expected_endpoints)


if __name__ == '__main__':
    log_format = '%(asctime)s:%(levelname)-7s:%(funcName)s:%(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
    unittest.main()
