"""
Templates for key parts of a Swagger-defined API which can be used to generate
specific API requests adhering to the definition.
"""
import logging

import valuetemplates as vts


log = logging.getLogger(__name__)


class BaseValueFactory:
    """Common factory for building ValueTemplates from swagger definitions."""

    @classmethod
    def create_value(cls, swagger_definition):
        """Create a ValueTemplate for the value specified by the definition.
        :type swagger_definition: pyswagger.spec.v2_0.objects.Parameter or
                                  pyswagger.spec.v2_0.objects.Items or
                                  pyswagger.spec.v2_0.objects.Schema
        """
        value = None
        if swagger_definition.type == 'boolean':
            value = cls._create_bool_value(swagger_definition)
        elif swagger_definition.type == 'integer':
            value = cls._create_integer_value(swagger_definition)
        elif swagger_definition.type == 'number':
            value = cls._create_float_value(swagger_definition)
        elif swagger_definition.type == 'string':
            if swagger_definition.format == 'date':
                value = cls._create_date_value(swagger_definition)
            elif swagger_definition.format == 'date-time':
                value = cls._create_datetime_value(swagger_definition)
            else:
                value = cls._create_string_value(swagger_definition)
        elif swagger_definition.type == 'file':
            value = cls._create_file_value(swagger_definition)
        elif swagger_definition.type == 'array':
            value = cls._create_array_value(swagger_definition)

        if value is None:
            raise ValueError("Unsupported type, format: {}, {}".format(
                swagger_definition.type, swagger_definition.format))

        return value

    @staticmethod
    def _create_bool_value(swagger_definition):
        return vts.BooleanTemplate()

    @staticmethod
    def _create_integer_value(swagger_definition):
        return vts.IntegerTemplate(
            maximum=swagger_definition.maximum,
            exclusive_maximum=swagger_definition.exclusiveMaximum,
            minimum=swagger_definition.minimum,
            exclusive_minimum=swagger_definition.exclusiveMinimum,
            multiple_of=swagger_definition.multipleOf)

    @staticmethod
    def _create_float_value(swagger_definition):
        return vts.FloatTemplate(
            maximum=swagger_definition.maximum,
            exclusive_maximum=swagger_definition.exclusiveMaximum,
            minimum=swagger_definition.minimum,
            exclusive_minimum=swagger_definition.exclusiveMinimum,
            multiple_of=swagger_definition.multipleOf)

    @staticmethod
    def _create_date_value(swagger_definition):
        return vts.DateTemplate()

    @staticmethod
    def _create_datetime_value(swagger_definition):
        return vts.DateTimeTemplate()

    @staticmethod
    def _create_file_value(swagger_definition):
        return vts.FileTemplate()

    @staticmethod
    def _create_string_value(swagger_definition):
        return vts.StringTemplate(
            max_length=swagger_definition.maxLength,
            min_length=swagger_definition.minLength,
            pattern=swagger_definition.pattern,
            enum=swagger_definition.enum)

    @staticmethod
    def _create_array_value(swagger_definition):
        return vts.ArrayTemplate(
            max_items=swagger_definition.maxItems,
            min_items=swagger_definition.minItems,
            unique_items=swagger_definition.uniqueItems)


class ParameterValueFactory(BaseValueFactory):
    """Factory for building ValueTemplates from Parameter definitions."""

    @staticmethod
    def _create_string_value(swagger_definition):
        if getattr(swagger_definition, 'in', '') == 'path':
            template_type = vts.URLPathStringTemplate
        elif getattr(swagger_definition, 'in', '') == 'header':
            template_type = vts.HTTPHeaderStringTemplate
        else:
            template_type = vts.StringTemplate
        return template_type(max_length=swagger_definition.maxLength,
                             min_length=swagger_definition.minLength,
                             pattern=swagger_definition.pattern,
                             enum=swagger_definition.enum)


class ModelValueFactory(BaseValueFactory):
    """Factory for building ValueTemplates from Model definitions."""

    @classmethod
    def create_value(cls, swagger_definition):
        if swagger_definition.type == 'object':
            return cls._create_object_value(swagger_definition)

        return super(ModelValueFactory, cls).create_value(swagger_definition)

    @staticmethod
    def _create_object_value(swagger_definition):
        log.debug("Properties: %r", swagger_definition.properties)
        # If there are no fixed properties then allow arbitrary ones to be
        # added.
        additional = (swagger_definition.additionalProperties not in
                      (None, False))
        additional = (additional or len(swagger_definition.properties) == 0)
        return vts.ObjectTemplate(
            max_properties=swagger_definition.maxProperties,
            min_properties=swagger_definition.minProperties,
            additional_properties=additional)


class BaseParameterTemplate:
    """Common base class for Swagger API operation paramters."""
    VALUE_FACTORY = BaseValueFactory

    def __init__(self, swagger_app, swagger_definition):
        self._swagger_app = swagger_app
        self._swagger_definition = swagger_definition
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
            self._children = self.__class__(self._swagger_app,
                                            self._swagger_definition.items)

    def _populate_value(self):
        self._value_template = self.VALUE_FACTORY.create_value(
            self._swagger_definition)

    @property
    def name(self):
        """The name of this parameter, if it has one.
        :rtype: str or None
        """
        return getattr(self._swagger_definition, 'name', None)

    @property
    def type(self):
        """The type of this parameter.
        :rtype: str
        """
        return self._swagger_definition.type

    @property
    def format(self):
        """The format of this parameter.
        :rtype: str
        """
        return self._swagger_definition.format

    @property
    def value_template(self):
        """The template for the value of this parameter.
        :rtype: valuetemplates.ValueTemplate
        """
        return self._value_template

    @property
    def children(self):
        """The children of this parameter - may be `None` if there are none.
        :rtype: ParameterTemplate or None
        """
        return self._children


class ParameterTemplate(BaseParameterTemplate):
    """Template for a parameter to pass to an operation on an endpoint.

    Since a Swagger `Items` object maybe a child of a `Parameter`, model that
    as a parameter as well since it's sufficiently similar we don't care about
    the distinction. `Items` don't have names though, so be careful of that.

    :type swagger_app: pyswagger.App
    :type swagger_definition: pyswagger.spec.v2_0.objects.Parameter or
                              pyswagger.spec.v2_0.objects.Items
    """
    VALUE_FACTORY = ParameterValueFactory


class ModelTemplate(BaseParameterTemplate):
    """Template for a generic parameter, which may be one of many types,
    defining the model it follows.

    In the Swagger/OpenAPI world, this maps to a `Schema Object`.

    :type swagger_app: pyswagger.App
    :type swagger_definition: pyswagger.spec.v2_0.objects.Schema
    """
    VALUE_FACTORY = ModelValueFactory

    def __init__(self, swagger_app, swagger_definition):
        super().__init__(swagger_app, self._resolve_schema(swagger_app,
                                                           swagger_definition))

    def _resolve_schema(self, app, schema):
        """If the schema for this model is a reference, dereference it."""
        ref = getattr(schema, '$ref')
        log.debug("Ref is: %r", ref)
        if ref is not None:
            schema = app.resolve(ref)
        log.debug("Schema: %r", schema)
        log.debug("Schema name: %r", schema.name)

        return schema

    def _populate_children(self):
        if self.type == 'object':
            log.debug("Properties: %r", self._swagger_definition.properties)
            self._children = {prop_name: self.__class__(self._swagger_app,
                                                        prop_value)
                              for prop_name, prop_value in
                              self._swagger_definition.properties.items()}

        super()._populate_children()


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
        :rtype: dict(str, BaseParameterTemplate)
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
                param_template = ParameterTemplate(self._app, parameter)
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
