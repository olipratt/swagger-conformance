import logging


log = logging.getLogger(__name__)


class ParameterTemplate:
    """Template for a parameter to pass to an operation on an endpoint."""

    def __init__(self, parameter):
        assert parameter.type is not None
        self._type = parameter.type
        assert parameter.name is not None
        self._name = parameter.name

    def __repr__(self):
        return "{}(name={}, type={})".format(self.__class__.__name__,
                                             self._name,
                                             self._type)

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type


class ModelTemplate:
    """Template for a generic parameter, which may be one of many types,
    defining the model it follows.

    In the Swagger/OpenAPI world, this maps to a `Schema Object`.
    """

    def __init__(self, app, schema):
        self._app = app
        self._schema = schema
        self._contents = None

        self._build()

    @property
    def contents(self):
        return self._contents

    def _build(self):
        # The object may actually be a reference to the definition - if so
        # resolve it.
        ref = getattr(self._schema, '$ref')
        log.debug("Ref is: %r", ref)
        if ref is not None:
            schema = self._app.resolve(ref)
        else:
            schema = self._schema
        log.debug("Schema: %r", schema)
        log.debug("Schema name: %r", schema.name)

        # Populate the model based on its type.
        if schema.type == 'object':
            # If this is an oject with no properties, treat it as a freeform
            # JSON object - which we leave denoted by None.
            log.debug("Properties: %r", schema.properties)
            if len(schema.properties) > 0:
                self._contents = {}
                for prop_name in schema.properties:
                    log.debug("This prop: %r", prop_name)
                    child = ModelTemplate(self._app,
                                          schema.properties[prop_name])
                    self._contents[prop_name] = child
        else:
            log.warning("SKIPPING SCHEMA TYPE: %r - NOT IMPLEMENTED",
                        schema.type)


class OperationTemplate:
    """Template for an operation on an endpoint."""

    def __init__(self, app, operation):
        self._app = app
        self._operation = operation
        self._parameters = {}

        self._populate_parameters()

    def __repr__(self):
        return "{}(operation={}, params={})".format(self.__class__.__name__,
                                                    self._operation,
                                                    self._parameters)

    @property
    def operation(self):
        return self._operation

    @property
    def parameters(self):
        return self._parameters

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
