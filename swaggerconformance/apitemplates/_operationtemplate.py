"""
Templates for key parts of a Swagger-defined API which can be used to generate
specific API requests adhering to the definition.
"""
import logging

from ._parametertemplate import ParameterTemplate
from ._swaggerparameter import SwaggerParameter
from ..strategies import merge_optional_dict_strategy

__all__ = ["OperationTemplate"]


log = logging.getLogger(__name__)


class OperationTemplate:
    """Template for an operation on an endpoint.

    :param operation: The definition of the operation in the API schema.
    :type operation: pyswagger.spec.v2_0.objects.Operation
    """

    def __init__(self, operation):
        self._operation = operation
        self._response_codes = None
        self._parameters = {}

        self._populate_response_codes()
        self._populate_parameters()

    def __repr__(self):
        return "{}(id={!r}, method={!r}, path={!r}, params={!r})".format(
            self.__class__.__name__, self.id, self.method, self.path,
            self._parameters)

    def hypothesize_parameters(self, value_factory):
        """Generate hypothesis fixed dictionary mapping of parameters.

        :param value_factory: Factory to generate strategies for values.
        :type value_factory: swaggerconformance.valuetemplates.ValueFactory
        """
        req_params = {param_name: param_template.hypothesize(value_factory)
                      for param_name, param_template in self.parameters.items()
                      if param_template.required}
        opt_params = {param_name: param_template.hypothesize(value_factory)
                      for param_name, param_template in self.parameters.items()
                      if not param_template.required}

        return merge_optional_dict_strategy(req_params, opt_params)

    @property
    def id(self):
        """The Swagger operationId of this operation.

        :rtype: str
        """
        return self._operation.operationId

    @property
    def path(self):
        """The path of this operation.

        :rtype: str
        """
        return self._operation.path

    @property
    def method(self):
        """The method of this operation.

        :rtype: str
        """
        return self._operation.method

    @property
    def parameters(self):
        """Mapping of the names of the parameters to their templates.

        :rtype: dict(str, ParameterTemplate)
        """
        return self._parameters

    @property
    def response_codes(self):
        """List of HTTP response codes this operation might return.

        :rtype: set(int)
        """
        return self._response_codes

    def _populate_response_codes(self):
        # 'default' is a special value to cover undocumented response codes:
        # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#fixed-fields-9
        # If only that value is specified, assume that any successful response
        # code is allowed.
        self._response_codes = {int(code) for code in self._operation.responses
                                if code != "default"}
        if len(self._response_codes) == 0:
            assert "default" in self._operation.responses, \
                "No response codes at all"
            log.warning("Only 'default' response defined - allowing any 2XX")
            self._response_codes = set(range(200, 300))
        if all((x > 299 or x < 200) for x in self._response_codes):
            log.warning("No success responses defined - allowing 200")
            self._response_codes.add(200)

    def _populate_parameters(self):
        for parameter in self._operation.parameters:
            log.debug("Handling parameter: %r", parameter.name)

            # Every parameter has a name. It's either a well defined parameter,
            # or it's the lone body parameter, in which case it's a Model
            # defined by a schema.
            if parameter.schema is None:
                log.debug("Fully defined parameter")
                template = ParameterTemplate(SwaggerParameter(parameter))
            else:
                log.debug("Schema defined parameter")
                template = ParameterTemplate(
                    SwaggerParameter(parameter.schema))

            self._parameters[parameter.name] = template

    @property
    def _pyswagger_operation(self):
        """The underlying pyswagger definition of the operation - useful
        elsewhere internally but not expected to be referenced external to the
        package.

        :rtype: pyswagger.spec.v2_0.objects.Operation
        """
        return self._operation
