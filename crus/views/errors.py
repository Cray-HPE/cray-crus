"""Error handling for the Tenant Managment Service API routes,
conforming to RFC 7807. Provides exceptions to raise when a particular
error is encountered nd error handlers for those errors..

Copyright 2019, Cray Inc. All rights reserved.

"""
from http import HTTPStatus as HS

from flask import Response
from httpproblem import problem_http_response

from ..app import APP


class RequestError(Exception):
    """Base Class for error handling exceptions

    """
    def __init__(self,
                 status_code=None,
                 title=None,
                 detail=None,
                 instance_type=None,
                 instance=None,
                 errors=None):
        """constructor, callled with the appropriate settings from the derived
        class

        param: status_code - the numeric status code of the response
        param: title - the title for the status staus code
        param: detail - the problem detail for the response
        param: instance_type - the 'type' of the response
        param: instance - provide an 'instance' for the reported problem
        param: errors - provide a list of errors to be included with the
               problem (list of strings).

        """
        Exception.__init__(self)
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type = instance_type
        self.instance = instance
        self.errors = errors

    def __str__(self):
        return self.title

    def response(self):
        """Compose a Flask response containing a body derived from

            httpproblem.problem_http_response()

        based on the information provided in the constructor.

        Returns: flask.Response object of an error in RFC 7807 format

        """
        problem = problem_http_response(status=self.status_code,
                                        title=self.title,
                                        detail=self.detail,
                                        type=self.type,
                                        instance=self.instance,
                                        errors=self.errors,
                                        headers=None)
        return Response(problem['body'],
                        status=problem['statusCode'],
                        headers=problem['headers'])


class MissingInput(RequestError):
    """No input was provided. Reports 400 - Bad Request.

    """

    def __init__(self,
                 status_code=None,
                 title=None,
                 detail=None,
                 instance_type=None,
                 instance=None,
                 errors=None):
        RequestError.__init__(self,
                              status_code=status_code or HS.BAD_REQUEST,
                              title=title or "Bad Request",
                              detail=detail or "No input provided. Determine "
                              "the specific information that is missing or "
                              "invalid and then re-run the request with "
                              "valid information.",
                              instance_type=instance_type,
                              instance=instance,
                              errors=errors)


class DataValidationFailure(RequestError):
    """Validation errors in input data. Reports 422 - Unprocessable entity

    """
    def __init__(self,
                 status_code=None,
                 title=None,
                 detail=None,
                 instance_type=None,
                 instance=None,
                 errors=None):
        RequestError.__init__(self,
                              status_code=status_code or HS.UNPROCESSABLE_ENTITY,
                              title=title or "Unprocessable Entity",
                              detail=detail or "Input data was understood, "
                              "but failed validation. Re-run request with "
                              "valid input values for the fields indicated "
                              "in the response.",
                              instance_type=instance_type,
                              instance=instance,
                              errors=errors)


class ResourceNotFound(RequestError):
    """Resource with given id was not found. Reports 404 - Not Found.

    """
    def __init__(self,
                 status_code=None,
                 title=None,
                 detail=None,
                 instance_type=None,
                 instance=None,
                 errors=None):
        RequestError.__init__(self,
                              status_code=status_code or HS.NOT_FOUND,
                              title=title or "Not Found",
                              detail=detail or "Requested resource does "
                              "not exist. Re-run request with valid ID.",
                              instance_type=instance_type,
                              instance=instance,
                              errors=errors)


class MethodNotAllowed(RequestError):
    """Requested resource does not support the specified method.  Reports
    405 - Method Not Allowed.

    """

    def __init__(self,
                 status_code=None,
                 title=None,
                 detail=None,
                 instance_type=None,
                 instance=None,
                 errors=None):
        RequestError.__init__(self,
                              status_code=status_code or HS.METHOD_NOT_ALLOWED,
                              title=title or "Method Not Allowed",
                              detail=detail or "Method not allowed. Determine "
                              "the resource used and the method requested and "
                              "then re-run the request with correct resource "
                              "and method.",
                              instance_type=instance_type,
                              instance=instance,
                              errors=errors)


# pylint: disable=unused-argument
@APP.errorhandler(HS.METHOD_NOT_ALLOWED)
def method_not_allowed(error):  # pragma should never happen
    """Error handler for disallowed methods arising outside the route code"""
    # Cheat for consistency and to avoid duplication.  We don't
    # actually want to raise an exception here, but by instantiating a
    # MethodNotAllowed we can use its response() method to compose the
    # response...
    err = MethodNotAllowed()
    return err.response()


@APP.errorhandler(RequestError)
def request_error(exc):
    """Error Handler for RequestErrors raised by route code """
    return exc.response()
