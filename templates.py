"""
Templates for key parts of a Swagger-defined API which can be used to generate
specific API requests adhering to the definition.
"""
import logging

import valuetemplates as vts


log = logging.getLogger(__name__)


class ParameterTemplate:
    """Template for a parameter to pass to an operation on an endpoint.

    Since a Swagger `Items` object maybe a child of a `Parameter`, model that
    as a parameter as well since it's sufficiently similar we don't care about
    the distinction. `Items` don't have names though, so be careful of that.

    :type parameter: pyswagger.spec.v2_0.objects.Parameter or
                     pyswagger.spec.v2_0.objects.Items
    """

    def __init__(self, parameter):
        self._parameter = parameter
        self._children = None
        self._value_template = None

        self._populate_value()
        self._populate_children()

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self.name,
                                             self.type)

    def _populate_children(self):
        if self.type == 'array':
            self._children = ParameterTemplate(self._parameter.items)

    def _populate_value(self):
        value = None
        if self.type == 'boolean':
            value = vts.BooleanTemplate()
        elif self.type in ['integer', 'number']:
            template_type = {'integer': vts.IntegerTemplate,
                             'number': vts.FloatTemplate}[self.type]
            value = template_type(
                maximum=self._parameter.maximum,
                exclusive_maximum=self._parameter.exclusiveMaximum,
                minimum=self._parameter.minimum,
                exclusive_minimum=self._parameter.exclusiveMinimum,
                multiple_of=self._parameter.multipleOf)
        elif self.type == 'string':
            if self.format == 'date':
                value = vts.DateTemplate()
            elif self.format == 'date-time':
                value = vts.DateTimeTemplate()
            else:
                if getattr(self._parameter, 'in', '') == 'path':
                    template_type = vts.URLPathStringTemplate
                elif getattr(self._parameter, 'in', '') == 'header':
                    template_type = vts.HTTPHeaderStringTemplate
                else:
                    template_type = vts.StringTemplate
                value = template_type(max_length=self._parameter.maxLength,
                                      min_length=self._parameter.minLength,
                                      pattern=self._parameter.pattern,
                                      enum=self._parameter.enum)
        elif self.type == 'array':
            value = vts.ArrayTemplate(max_items=self._parameter.maxItems,
                                      min_items=self._parameter.minItems,
                                      unique_items=self._parameter.uniqueItems)
        elif self.type == 'file':
            value = vts.FileTemplate()

        assert value is not None, "Unsupported type: {}".format(self.type)
        self._value_template = value

    @property
    def name(self):
        """The name of this parameter, if it has one.
        :rtype: str or None
        """
        return getattr(self._parameter, 'name', None)

    @property
    def type(self):
        """The type of this parameter.
        :rtype: str
        """
        return self._parameter.type

    @property
    def value_template(self):
        """The template for the value of this parameter.
        :rtype: valuetemplates.ValueTemplate
        """
        return self._value_template

    @property
    def is_path(self):
        """Does this parameter appear in the URL path?
        :rtype: bool
        """
        return getattr(self._parameter, 'in', '') == 'path'

    @property
    def is_header(self):
        """Does this parameter appear in a header?
        :rtype: bool
        """
        return getattr(self._parameter, 'in', '') == 'header'

    @property
    def enum(self):
        """The valid enum values of this parameter.
        :rtype: list(str)
        """
        return self._parameter.enum

    @property
    def format(self):
        """The format of this parameter.
        :rtype: str
        """
        return self._parameter.format

    @property
    def children(self):
        """The children of this parameter - may be `None` if there are none.
        :rtype: ParameterTemplate or None
        """
        return self._children


class ModelTemplate:
    """Template for a generic parameter, which may be one of many types,
    defining the model it follows.

    In the Swagger/OpenAPI world, this maps to a `Schema Object`.

    :type app: pyswagger.App
    :type schema: pyswagger.spec.v2_0.objects.Schema
    """

    def __init__(self, app, schema):
        self._app = app
        self._schema = self._resolve_schema(schema)
        self._children = None

        self._populate_children()

    @property
    def children(self):
        """The children of this model - may be `None` if there are none.
        :rtype: dict or ModelTemplate or None
        """
        return self._children

    @property
    def type(self):
        """The type of this model.
        :rtype: str
        """
        return self._schema.type

    @property
    def format(self):
        """The format of this model.
        :rtype: str
        """
        return self._schema.format

    @property
    def enum(self):
        """The valid enum values of this model.
        :rtype: list
        """
        return self._schema.enum

    def _resolve_schema(self, schema):
        """If the schema for this model is a reference, dereference it."""
        ref = getattr(schema, '$ref')
        log.debug("Ref is: %r", ref)
        if ref is not None:
            schema = self._app.resolve(ref)
        log.debug("Schema: %r", schema)
        log.debug("Schema name: %r", schema)

        return schema

    def _populate_children(self):
        assert self._schema.type in ['object', 'integer', 'number', 'string',
                                     'boolean', 'array']

        # Populate the model children based on its type.
        if self._schema.type == 'object':
            # If this is an oject with no properties, treat it as a freeform
            # JSON object - which we leave denoted by None.
            log.debug("Properties: %r", self._schema.properties)
            if len(self._schema.properties) > 0:
                self._children = {}
                for prop_name in self._schema.properties:
                    log.debug("This prop: %r", prop_name)
                    child = ModelTemplate(self._app,
                                          self._schema.properties[prop_name])
                    self._children[prop_name] = child
        elif self._schema.type == 'array':
            log.debug("Model is array")
            self._children = ModelTemplate(self._app, self._schema.items)


class OperationTemplate:
    """Template for an operation on an endpoint.
    :type app: pyswagger.App
    :type operation: pyswagger.spec.v2_0.objects.Operation
    """

    def __init__(self, app, operation):
        self._app = app
        self._operation = operation
        self._parameters = {}
        # 'default' is a special value to cover undocumented response codes:
        # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#fixed-fields-9
        # If only that value is specified, assume that any successful response
        # code is allowed.
        self._response_codes = [int(code) for code in operation.responses
                                if code != "default"]
        if len(self._response_codes) == 0:
            assert "default" in operation.responses, "No response codes at all"
            log.warning("Only 'default' response defined - allowing any 2XX")
            self._response_codes = list(range(200, 300))
        if all((x > 299 or x < 200) for x in self._response_codes):
            log.warning("No success responses defined - allowing 200")
            self._response_codes.append(200)

        self._populate_parameters()

    def __repr__(self):
        return "{}(operation={}, params={})".format(self.__class__.__name__,
                                                    self._operation,
                                                    self._parameters)

    @property
    def operation(self):
        """The actual API operation this template represents.
        :rtype: pyswagger.spec.v2_0.objects.Operation
        """
        return self._operation

    @property
    def parameters(self):
        """Mapping of the names of the parameters to their templates.
        :rtype: dict(str, ParameterTemplate)
        """
        return self._parameters

    @property
    def response_codes(self):
        """List of HTTP response codes this operation might return.
        :rtype: list(int)
        """
        return self._response_codes

    def _populate_parameters(self):
        for parameter in self._operation.parameters:
            log.debug("Handling parameter: %r", parameter.name)

            # Every parameter has a name. It's either a well defined parameter,
            # or it's the lone body parameter, in which case it's a Model
            # defined by a schema.
            if parameter.name == 'X-Fields':
                log.warning("SKIPPING X-Fields PARAM - NOT IMPLEMENTED")
            elif parameter.schema is None:
                log.debug("Fully defined parameter")
                param_template = ParameterTemplate(parameter)
                self._parameters[parameter.name] = param_template
            else:
                log.debug("Schema defined parameter")
                model_template = ModelTemplate(self._app, parameter.schema)
                self._parameters[parameter.name] = model_template


class APITemplate:
    """Template for an entire Swagger API.
    :type client: client.SwaggerClient
    """

    operations = ["get", "put", "post", "delete"]

    def __init__(self, client):
        log.debug("Creating new endpoint collection for: %r", client)
        self._client = client
        self._app = client.app

        self._paths = self._app.root.paths.keys()
        log.debug("Found paths as: %s", self._paths)

        self._expanded_paths = {}
        for path in self._paths:
            self._expanded_paths[path] = self._expand_path(path)

    @property
    def endpoints(self):
        """Mapping of the endpoints of this API to their operations.
        :rtype: dict
        """
        return self._expanded_paths

    def iter_template_operations(self):
        """All operations of the API across all endpoints.

        :yields: OperationTemplate
        """
        for endpoint in self.endpoints:
            log.debug("Testing endpoint: %r", endpoint)
            for operation_type in self.endpoints[endpoint]:
                log.debug("Testing operation type: %r", operation_type)
                operation = self.endpoints[endpoint][operation_type]
                log.info("Got operation: %r", operation)

                yield operation

    def _expand_path(self, path):
        log.debug("Expanding path: %r", path)

        operations_map = {}
        for operation_name in self.operations:
            log.debug("Accessing operation: %s", operation_name)
            operation = getattr(self._app.root.paths[path], operation_name)
            if operation is not None:
                log.debug("Have operation")
                operations_map[operation_name] = OperationTemplate(self._app,
                                                                   operation)

        log.debug("Expanded path as: %r", operations_map)
        return operations_map
