"""
Example test using `swaggerconformance`. Drives a simple datastore API that
lets you store some data with a key (in the form of a JSON object / Python
dict), retrieve it later, and delete it.

You must first start the `datastore_api.py` file running in another terminal
before running this test, as it will send requests to that server which will by
default expose the API at `http://127.0.0.1:5000/api/`. You can view the API at
`http://127.0.0.1:5000/` to see what it exposes.

**Running this test should fail - see the comment at the end of the file for
an explanation why. Before reading that though, it's worth looking at the code
below and the output from running it, and trying to spot the reason why - the
bug is in the code in this file, so you can ignore the code in
`datastore_api.py`.**
"""
import hypothesis
import swaggerconformance

# Create the client to access the API, and templates for the API operations.
# (Add a try/except to try and catch when a user hasn't started the server).
try:
    schema_url = 'http://127.0.0.1:5000/api/schema'
    client = swaggerconformance.SwaggerClient(schema_url)
except:
    raise Exception("Failed to load API schema - have you started the server?")

api_template = swaggerconformance.APITemplate(client)

# Get references to the operations we'll use for testing, and strategies for
# generating inputs to those operations.
value_factory = swaggerconformance.ValueFactory()
put_operation = api_template.endpoints["/apps/{appid}"]["put"]
put_strategy = put_operation.hypothesize_parameters(value_factory)
get_operation = api_template.endpoints["/apps/{appid}"]["get"]
get_strategy = get_operation.hypothesize_parameters(value_factory)

# Hypothesis will generate values fitting the strategies that define the
# parameters to the chosen operations. The decorated function is then called
# the chosen number of times with the generated parameters provided as the
# final arguments to the function.
@hypothesis.settings(max_examples=200)
@hypothesis.given(put_strategy, get_strategy)
def single_operation_test(client, put_operation, get_operation,
                          put_params, get_params):
    """PUT a new app with some data, then GET the data again and verify it
    matches what was just sent in."""
    # Use the client to make a request with the generated parameters, and
    # assert this returns a valid response.
    response = client.request(put_operation, put_params)
    assert response.status in put_operation.response_codes, \
        "{} not in {}".format(response.status, put_operation.response_codes)

    # The parameters are just dictionaries with string name keys and correct
    # format values.
    # We generated two independent sets of parameters, so replace the id in the
    # second set with the id from the first so they reference the same object.
    get_params["appid"] = put_params["appid"]
    response = client.request(get_operation, get_params)

    # `response.data` contains the JSON body of the response converted to
    # Python objects.
    # `payload` is always the name of body parameters on requests.
    out_data = response.data.data
    in_data = put_params["payload"]["data"]
    # This assert should fail if hypothesis has enough attempts - see the
    # `EXPLANATION OF BUG` section at the end of the file for why!
    assert out_data == in_data, "{!r} != {!r}".format(out_data, in_data)

# Finally, remember to call the test function to run the tests, and that
# hypothesis provides the generated parameter arguments.
single_operation_test(client, put_operation, get_operation) # pylint: disable=I0011,E1120


# EXPLANATION OF BUG
# ------------------
# The failure is in the comparison in the assert. The output from running the
# test should be something like:
#     AssertionError: {'': None, '1': None, '0': None, '3': None, '2': nan} !=
#     {'': None, '0': None, '1': None, '3': None, '2': nan}
# `hypothesis` has done it's best to simplify the failure down, and glancing
# at it these things do look equal, but the culprit is the `nan` - in the IEEE
# standard it's defined that the following must hold:
#     >>> float("nan") == float("nan")
#     False
# So we need a better way of checking that our input and output `dict`s are
# equal than just `==`!
