import logging
import unittest

import responses

import swaggertester

TEST_SCHEMA_PATH = 'test_schema.json'
SCHEMA_URL_BASE = 'http://127.0.0.1:5000/api'
CONTENT_TYPE_JSON = 'application/json'


class EndpointCollectionTestCase(unittest.TestCase):

    def setUp(self):
        self.client = swaggertester.SwaggerClient(TEST_SCHEMA_PATH)

    def tearDown(self):
        # No teardown of test fixtures required.
        pass

    def test_schema_parse(self):
        endpoints_clctn = swaggertester.EndpointCollection(self.client)
        expected_endpoints = {'/schema', '/apps', '/apps/{appid}'}
        self.assertSetEqual(set(endpoints_clctn.endpoints.keys()),
                            expected_endpoints)

    @responses.activate
    def test_endpoint(self):
        endpoints_clctn = swaggertester.EndpointCollection(self.client)
        endpoint = endpoints_clctn.endpoints['/apps/{appid}']
        self.assertIn('get', endpoint)
        endpoint_op = endpoint['get']
        self.assertEqual(len(endpoint_op.parameters), 1)
        self.assertEqual(endpoint_op.parameters['appid'].type, 'string')
        params = {'appid': 'test_string'}

        responses.add(responses.GET, SCHEMA_URL_BASE + '/apps/test_string',
                      json={}, status=404,
                      content_type=CONTENT_TYPE_JSON)
        result = self.client.request(endpoint_op, params)
        self.assertEqual(result.status, 404)


if __name__ == '__main__':
    log_format = '%(asctime)s:%(levelname)-7s:%(funcName)s:%(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
    unittest.main()
