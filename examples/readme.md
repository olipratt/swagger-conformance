# Examples

Examples showing how to use this package.

## Getting Started

The simplest way to test your API is just to ask `swaggerconformance` to validate it as follows (assuming your swagger spec is hosted at `http://example.com/api/schema.json` - a local file path could be used instead):

```python
from swaggerconformance import api_conformance_test

api_conformance_test('http://example.com/api/schema.json')
```

This will simply make requests against your API using data generated to match your API schema, and ensure that the response codes and data returned also match your schema.

### Handling Failures

If this testing fails, you'll be shown an example input to an API operation which resulted in a response that didn't match your schema. Something like:

```
Falsifying example: single_operation_test(
    client=SwaggerClient(schema_path='http://example.com/api/schema.json'),
    operation=OperationTemplate(
        method='get',
        path='/example/{exint}',
        params={'exint': ParameterTemplate(name='exint', type='integer', required=True)}),
    params={'exint': -1})
...
<Some stack trace here>
...
AssertionError: Response code 500 not in {200, 404}
```

This shows that when testing the `GET` operation on the endpoint `/example/{exint}`, using the value `-1` for `exint` resulted in a `500` response code from the server, which is not one of the documented response codes (and any `5XX` response code is clearly an error!). From this we can tell that this server isn't handling negative numbers for this parameter properly and needs to be made more robust.

_As an aside, one great feature of hypothesis is once it finds a failing example, it will simplify it down as far as it can. So here it might have first found that_ `-2147483648` _failed, but instead of just reporting that and let you figure out if that number is special, it tries to find the simplest failing input value, e.g. here reducing down to simply_ `-1`_._

## Targeted and Stateful Testing

The basic testing above just throws data at your API, but it's useful to be able to target specific endpoints, or build sequenced tests where the output of one operation is used as the input to another.

### Example

Here's a small example of a test that creates a resource with a `PUT` containing some generated data, and then verifies that a `GET` returns the exact same data.

You can run this test yourself by starting the `datastore_api.py` server and running the `ex_targeted_test.py` script in the [examples directory](https://github.com/olipratt/swagger-conformance/tree/master/examples). A walkthrough of the code there follows.

### Walkthrough

The first part of the setup involves creating a client that will make requests against the API, and creating templates for all operations and parameters the API exposes. The client can be given a URL or local file path to read the schema from.

```python
import hypothesis
import swaggerconformance

# Create the client to access the API and to template the API operations.
schema_url = 'http://127.0.0.1:5000/api/schema'
client = swaggerconformance.client.SwaggerClient(schema_url)
```

The next step pulls out the operations that will be tested, and creates `hypothesis` strategies for generating inputs to them. Here specific operations are accessed, but it's possible to just iterate through all operations in `client.api.template_operations()`. The `value_factory` generates strategies for individual data types being used - we'll just use the defaults, but the next section covers adding your own extra data types.

```python
# Get references to the operations we'll use for testing, and strategies for
# generating inputs to those operations.
value_factory = swaggerconformance.valuetemplates.ValueFactory()
put_operation = client.api.endpoints["/apps/{appid}"]["put"]
put_strategy = put_operation.hypothesize_parameters(value_factory)
get_operation = client.api.endpoints["/apps/{appid}"]["get"]
get_strategy = get_operation.hypothesize_parameters(value_factory)
```

That's all the setup done - now to write the `hypothesis` test. The [hypothesis docs](http://hypothesis.readthedocs.io/en/latest/quickstart.html#writing-tests) go through details of doing this and the [available test settings](http://hypothesis.readthedocs.io/en/latest/settings.html#module-hypothesis). In short though, you write a function which validates the property of your API you want to verify, and through a decorator `hypothesis` runs this function multiple times. Each attempt uses different parameter values chosen to test all corners of the allowed values - the more attempts you allow `hypothesis`, the more thorough it can be and the greater the chance it has to flush out bugs.

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

`swaggerconformance` supports generating values for [all the standard datatypes from the OpenAPI schema](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#data-types). However you might have defined your own more specific ones and want to generate instances of them to get more thorough testing of valid inputs to your API.

### Example

For example, suppose you have an API operation that takes a colour as a parameter, so you've defined a new datatype for your API as:

|Common Name|`type`|`format`|Comments|
|-----------|------|--------|--------|
|colour|`string`|`hexcolour`|`#` and six hex chars, e.g. `#3FE7D9`|

By default, clearly `swaggerconformance` won't know what this `format` is, and will just generate `string` type data as input for parameters of this format. So for most requests, your API will just rejecting them with some `4XX` response because the parameter isn't of the correct format. You might prefer that valid hex colours were being generated to test a greater number of successful API requests. New `type` and `format` support can be added into `swaggerconformance` fairly easily.

The first step here is to create a `ValueTemplate` which can build a hypothesis strategy to generate these `hexcolour` values:

```python
import string
import hypothesis.strategies as hy_st
from swaggerconformance import valuetemplates

class HexColourTemplate(valuetemplates.ValueTemplate):
    """Template for a hex colour value."""

    def __init__(self, enum=None):
        # Various parameters like length don't make sense for this field, but
        # an enumeration of valid values may still be provided.
        super().__init__()
        self._enum = enum

    def hypothesize(self):
        # If there's a specific set of allowed values, the strategy should
        # return one of those.
        if self._enum is not None:
            return hy_st.sampled_from(self._enum)

        # We'll generate values as strings, but we could generate integers and
        # convert those to hex instead.
        strategy = hy_st.text(alphabet=set(string.hexdigits),
                              min_size=6,
                              max_size=6)
        # Don't forget to add the leading `#`.
        strategy = strategy.map(lambda x: "#" + x)

        return strategy
```

New `ValueTemplate`s just needs to provide a `hypothesize(self)` method which returns a `hypothesis` strategy - `__init__` is optional if no parameters are needed.

You can see the [hypothesis docs](http://hypothesis.readthedocs.io/en/latest/data.html) for more information on building up strategies. One written, you can test values your template will produce - e.g.:

```python
>>> template = HexColourTemplate()
>>> strategy = template.hypothesize()
>>> strategy.example()
'#CafB0b'
```

Now that the template for values of this type is defined, we just need to create an updated factory that will generate them. To do this, inherit from the built in one, and add logic into an overridden `create_value` method:

```python
import swaggerconformance

class HexColourValueFactory(swaggerconformance.valuetemplates.ValueFactory):
    def create_value(self, swagger_definition):
        """Handle `hexcolour` string format, otherwise defer to parent class.
        :type swagger_definition:
            swaggerconformance.apitemplates.SwaggerParameter
        """
        if (swagger_definition.type == 'string' and
                swagger_definition.format == 'hexcolour'):
            return HexColourTemplate(swagger_definition.enum)
        else:
            return super().create_value(swagger_definition)
```

Now whenever creating strategies for generating parameters for operations, use the new factory. Then anytime `string`, `hexcolour` is the datatype of a parameter, the new template will be used to generate a strategy for it. So in the example code in the previous section, the change would just be:

```python
schema_url = 'http://example.com/api/schema.json'
client = swaggerconformance.client.SwaggerClient(schema_url)

value_factory = HexColourValueFactory()  # Use enhanced factory for values.
put_operation = client.api.endpoints["/apps/{appid}"]["put"]
put_strategy = put_operation.hypothesize_parameters(value_factory)
...
```

There's no reason that the factory couldn't check other properties of the parameter to decide what type of values to generate, e.g. the `name` - but remember that likely clients won't have whatever special logic you add here so it may be better to assign a special data type instead.

If needed, you can replace any of the built in value templates - e.g. to restrict the alphabet of all generated basic strings - but again remember that making the generation more restrictive might mean bugs are missed if clients don't have the same restrictions.
