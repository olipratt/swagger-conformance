# Examples

Examples showing how to use this package.

## Getting Started

The simplest way to test your API is just to ask `swaggerconformance` to validated it as follows (assuming your swagger spec is hosted at `http://example.com/api/schema.json`):

```python
from swaggerconformance import validate_schema

validate_schema('http://example.com/api/schema.json')
```

This will simply make requests against your API using data generated to match your API schema, and ensure that the response codes and data returned also match your schema.

### Handling Failures

If this testing fails, you'll be shown a an example input to an API operation which resulted in a response that didn't match your schema. Something like:

```
Falsifying example: single_operation_test(
    client=SwaggerClient(schema_path='http://example.com/api/schema.json'),
    operation=OperationTemplate(
        method='get',
        path='/example/{exint}',
        params={'exint': ParameterTemplate(name='exint', type='integer', required=True)}),
    params={'exint': -1})
...
AssertionError: Response code 500 not in {200, 404}
```

This shows that when testing the `GET` operation on the endpoint `/example/{exint}`, using the value `-1` for `exint` resulted in a `500` response code from the server, which is not one of the documented response codes (and any `5XX` response code is clearly an error!). From this it seems this server isn't handling negative numbers for this parameter well and needs to be made more robust.

_As an aside, one great feature of hypothesis is once it finds a failing example, it will simplify it down as far as it can. So here it might have first found that `-2147483648` failed, but instead of just reporting that and let you figure out if that number is special it tries to find the simplest failing input value, e.g. here reducing down to simply `-1`._

## Targeted and Stateful Testing

The basic testing above just throws data at your API, but it's useful to be able to target specific endpoints, or build sequenced tests where the output of one operation is used as the input to another operation.

Here's a small example of a test that creates a resource with `PUT` containing some generated data, and then verifies a `GET` returns the exact same data.

You can run this test yourself by starting the `datastore_api.py` server and running the `ex_targeted_test.py` script in this directory, and read the same code there.

The first part of the setup involves creating a client that will make requests against the API, and creating templates for all operations and parameters the API exposes. The client can be given a URL or local file to read the schema from.

```python
import hypothesis
import swaggerconformance

# Create the client to access the API, and templates for the API operations.
client = swaggerconformance.SwaggerClient('http://example.com/api/schema.json')
api_template = swaggerconformance.APITemplate(client)
```

Now pull out the operations that will be tested, and `hypothesis` strategies for generating inputs to them. Here specific operations are accessed, but it's possible to just iterate through all operations in `api_template.template_operations()`. The value_factory generates strategies for individual data types being used - we'll just use the defaults, but the next section covers adding your own extra data types.

```python
# Get references to the operations we'll use for testing, and strategies for
# generating inputs to those operations.
value_factory = swaggerconformance.ValueFactory()
put_operation = api_template.endpoints["/apps/{appid}"]["put"]
put_strategy = put_operation.hypothesize_parameters(value_factory)
get_operation = api_template.endpoints["/apps/{appid}"]["get"]
get_strategy = get_operation.hypothesize_parameters(value_factory)
```

That's all the setup - now write the `hypothesis` test. The [`hypothesis` docs](http://hypothesis.readthedocs.io/en/latest/quickstart.html#writing-tests) go through details of doing this and the [available settings](http://hypothesis.readthedocs.io/en/latest/settings.html#module-hypothesis). In short though, write a function which validates the property of your API you want to verify, and `hypothesis` runs this test multiple times. Each attempt uses different parameter values chosen to test all corners of the allowed values - the more attempts you allow it, the more thorough it can be and the greater the opportunity it has to flush out bugs.

```python
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
    assert out_data == in_data, "{!r} != {!r}".format(out_data, in_data)

# Finally, remember to call the test function to run the tests, and that
# hypothesis provides the generated parameter arguments.
single_operation_test(client, put_operation, get_operation)
```

## Custom Data Types

`swaggerconformance` supports [all the standard datatypes from the OpenAPI schema](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#data-types), however you might have defined your own more specific ones and want to generate instances of them to get more thorough testing of valid inputs to your API.

...
