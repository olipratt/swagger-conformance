# swagger-conformance

You have a Swagger (aka OpenAPI) schema defining an API you provide - but does your API really conform to that schema, and does it correctly handle all valid inputs?

`swaggerconformance` combines the power of `hypothesis` for property based / fuzz testing with `pyswagger` to explore all corners of your API - testing its conformance to its specification.

## Purpose

A Swagger/OpenAPI Spec allows you to carefully define what things are and aren't valid for your API to consume and produce. This tool takes that definition, and tries to make requests exploring all parts of the API while strictly adhering to the schema. Its aim is to find any places where your application fails to adhere to its own spec, or even just falls over entirely, so you can fix them up.

_This is not a complete fuzz tester of your HTTP interface e.g. sending complete garbage, or to non-existent endpoints, etc. It's aiming to make sure that any valid client, using your API exactly as you specify, can't break it._

## Setup

Either install with `pip install swagger-conformance`, or manually clone this repository and from inside it install dependencies with `pip install -r requirements.txt`.

## Usage

After setup the simplest test you can run against your API is just:

```python
from swaggerconformance import api_conformance_test
api_conformance_test('http://example.com/api/schema.json')
```

where the URL should resolve to your swagger schema, or it can be a path to the file on disk.

This basic test tries all your API operations looking for errors. For explanation of the results and running more thorough tests, including sequences of API calls and defining your custom data types, [see the examples](https://github.com/olipratt/swagger-conformance/tree/master/examples).

## Wait, I don't get it, what does this thing do?

In short, it lets you generate example values for parameters to your Swagger API operations, make API requests using these values, and verify the responses.

For example, take the standard [petstore API](http://petstore.swagger.io/) example. At the time of writing, that has an endpoint `/pet` with a `PUT` method operation that takes a relatively complicated `body` parameter.

With just a little code, we can load in the swagger schema for that API, access the operation we care about, and generate example parameters for that operation:

```python
>>> import swaggerconformance
>>>
>>> client = swaggerconformance.SwaggerClient('http://petstore.swagger.io/v2/swagger.json')
>>> api_template = swaggerconformance.APITemplate(client)
>>>
>>> value_factory = swaggerconformance.ValueFactory()
>>> operation = api_template.endpoints["/pet"]["put"]
>>> strategy = operation.hypothesize_parameters(swaggerconformance.ValueFactory())
>>> strategy.example()
{
  'body':{
    'id':110339,
    'name':'\U00052ea5\x9d\ua79d\x92\x13\U000f7c436!\U000aa3c5R\U0005b40e\n',
    'photoUrls':[
      '\ua9d9\U0003fb3a\x13\U00025c1c\U000974a8\u3497\U000515fa\n',
      "\U000b38a4>*\u6683'\U0002cd8f\x0f\n"
    ],
    'status':'sold',
    'category':{
      'id':-22555826027447
    },
    'tags':[
      {
        'id':-172930,
        'name':'\U000286df\u04dc\U00033563\u696d\U00055ba8\x89H'
      }
    ]
  }
}
>>>
```

See [the examples](https://github.com/olipratt/swagger-conformance/tree/master/examples) for more details, and how to make requests against an API using these parameter values.
