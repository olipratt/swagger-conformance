# swagger-conformance

You have a Swagger (OpenAPI) schema defining the API you provide - but do you really conform to that schema, and do you correctly handle all inputs to it?

`swagger-conformance` combines the power of `hypothesis` for property based / fuzz testing with `pyswagger` to explore all parts of your API - demonstrating your API's conformance to your API specification.

## Purpose

A Swagger/OpenAPI Spec allows you to define what things are and aren't valid for your API to consume and produce. This tool takes that definition, and tries to explore all parts of it while strictly adhering to it. The aim is then to find any places where your application fails to adhere to its own spec, or even just falls over entirely.

_This is **not** a pure fuzz tester of your HTTP API e.g. sending complete garbage, or to non-existent endpoints - it's not aiming to test your framework in that way, instead making sure that any valid endpoint, using your API exactly as you specify, can't break it._

## Setup

Just clone this repository, and from inside it run:

```shell
$ pip install -r requirements.txt
```

## Usage

After setup the simplest test you can run against your API is just:

```python
from swaggerconformance import validate_schema
validate_schema('http://example.com/api/schema.json')
```

where the URL should resolve to your swagger schema, or it can be a path to the file on disk.

For more explanation of results and running more thorough tests, [see the examples](examples/readme.md).
