import logging
import unittest
import re
import os.path as osp

import responses

import swaggertester

TEST_SCHEMA_DIR = osp.relpath(osp.join(osp.dirname(osp.realpath(__file__)),
                                       'test_schemas/'))
TEST_SCHEMA_PATH = osp.join(TEST_SCHEMA_DIR, 'test_schema.json')
FULL_PUT_SCHEMA_PATH = osp.join(TEST_SCHEMA_DIR, 'full_put_schema.json')
PETSTORE_SCHEMA_PATH = osp.join(TEST_SCHEMA_DIR, 'petstore.json')
SCHEMA_URL_BASE = 'http://127.0.0.1:5000/api'
CONTENT_TYPE_JSON = 'application/json'


class APITemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.client = swaggertester.SwaggerClient(TEST_SCHEMA_PATH)

    def tearDown(self):
        # No teardown of test fixtures required.
        pass

    def test_schema_parse(self):
        endpoints_clctn = swaggertester.APITemplate(self.client)
        expected_endpoints = {'/schema', '/apps', '/apps/{appid}'}
        self.assertSetEqual(set(endpoints_clctn.endpoints.keys()),
                            expected_endpoints)

    @responses.activate
    def test_endpoint_manually(self):
        api_template = swaggertester.APITemplate(self.client)

        # Find the template GET operation on the /apps/{appid} endpoint.
        app_id_get_op = None
        for operation_template in api_template.iter_template_operations():
            if (operation_template.operation.method == 'get' and
                    operation_template.operation.path == '/apps/{appid}'):
                self.assertIsNone(app_id_get_op)
                app_id_get_op = operation_template
        self.assertIsNotNone(app_id_get_op)

        # The operation takes one parameter, 'appid', which is a string.
        self.assertEqual(list(app_id_get_op.parameters.keys()), ['appid'])
        self.assertEqual(app_id_get_op.parameters['appid'].type, 'string')

        # Send an example parameter in to the endpoint manually, catch the
        # request, and respond.
        params = {'appid': 'test_string'}
        responses.add(responses.GET, SCHEMA_URL_BASE + '/apps/test_string',
                      json={}, status=404,
                      content_type=CONTENT_TYPE_JSON)
        result = self.client.request(app_id_get_op, params)
        self.assertEqual(result.status, 404)


class ParameterTypesTestCase(unittest.TestCase):

    @responses.activate
    def test_full_put(self):
        # Handle all the basic endpoints.
        responses.add(responses.GET, SCHEMA_URL_BASE + '/schema',
                      json=None, status=200,
                      content_type=CONTENT_TYPE_JSON)
        responses.add(responses.GET, SCHEMA_URL_BASE + '/example',
                      json=None, status=200,
                      content_type=CONTENT_TYPE_JSON)
        responses.add(responses.DELETE, SCHEMA_URL_BASE + '/example',
                      json=None, status=204,
                      content_type=CONTENT_TYPE_JSON)

        # Handle the PUT requests on the endpoint which expects an integer path
        # parameter. Don't validate the body as we expect pyswagger to do so.
        url_re = re.compile(SCHEMA_URL_BASE + r'/example/-?\d+')
        responses.add(responses.PUT, url_re,
                      json=None, status=204,
                      content_type=CONTENT_TYPE_JSON)

        # Now just kick off the validation process.
        swaggertester.validate_schema(FULL_PUT_SCHEMA_PATH)

@unittest.skip
class ExternalExamplesTestCase(unittest.TestCase):

    @responses.activate
    def test_swaggerio_petstore(self):
        # Handle all the basic endpoints.
        responses.add(responses.GET, SCHEMA_URL_BASE + '/pet',
                      json=None, status=200,
                      content_type=CONTENT_TYPE_JSON)
        responses.add(responses.GET, SCHEMA_URL_BASE + '/store',
                      json=None, status=200,
                      content_type=CONTENT_TYPE_JSON)
        responses.add(responses.GET, SCHEMA_URL_BASE + '/user',
                      json=None, status=200,
                      content_type=CONTENT_TYPE_JSON)

        # Handle the PUT requests on the endpoint which expects an integer path
        # parameter. Don't validate the body as we expect pyswagger to do so.
        url_re = re.compile(SCHEMA_URL_BASE + r'/example/-?\d+')
        responses.add(responses.PUT, url_re,
                      json=None, status=204,
                      content_type=CONTENT_TYPE_JSON)

        # Now just kick off the validation process.
        swaggertester.validate_schema(PETSTORE_SCHEMA_PATH)

if __name__ == '__main__':
    LOG_FORMAT = '%(asctime)s:%(levelname)-7s:%(funcName)s:%(message)s'
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
    unittest.main()
