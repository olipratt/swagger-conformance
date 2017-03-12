# swagger-conformance

You have a Swagger (OpenAPI) schema defining the API you claim to provide - but do you really conform to it, and do you actually support all aspects of it?

`swagger-conformance` combines the power of `hypothesis` for property based / fuzz testing with `pyswagger` to explore all parts of your API - demonstrating your conformance to your API specification.

## Purpose

A Swagger/OpenAPI Spec allows you to define what things are and aren't valid for your API to consume/produce very broadly or specifically. This tool takes that definition, and tries to explore all parts of it while strictly adhering to it. The aim is then to find any places where your application fails to adhere to its own spec, or just fails entirely.

This is **not** a pure fuzz tester of your HTTP API e.g. sending complete garbage, or to non-existent endpoints - it's not aiming to test your framework in that way, instead making sure that any valid endpoint, using your API exactly as you specify, can't break it.

## Setup
Just run:

```shell
$ pip install -r requirements.txt
```

## Usage

After setup you can run with ...

## Todo

- More tests
- Support for more object types
- Add a DSL of some kind (JSON based?) for writing more complicated tests (e.g. send data to this operation, then request it on this other one, and assert the values stay the same)


