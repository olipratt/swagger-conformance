"""
Templates for key parts of a Swagger-defined API which can be used to generate
specific API requests adhering to the definition.
"""
import logging

from .parametertemplate import ParameterTemplate, ModelTemplate


log = logging.getLogger(__name__)


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
