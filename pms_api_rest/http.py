from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    NotFound,
    Unauthorized,
)

from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import SessionExpiredException
from odoo.loglevels import ustr

from odoo.addons.base_rest.http import RestApiDispatcher, wrapJsonException


class RestApiDispatcherPms(RestApiDispatcher):
    def __init__(self, httprequest):
        super().__init__(httprequest)

    def handle_error(self, exception):
        """Called within an except block to allow converting exceptions
        to abitrary responses. Anything returned (except None) will
        be used as response."""
        if isinstance(exception, SessionExpiredException):
            # we don't want to return the login form as plain html page
            # we want to raise a proper exception
            return wrapJsonException(Unauthorized(ustr(exception)))
        # try:
        #     return super(RestApiDispatcher, self).handle_error(exception)
        if isinstance(exception, MissingError):
            extra_info = getattr(exception, "rest_json_info", None)
            return wrapJsonException(
                NotFound(ustr(exception)),
                include_description=True,
                extra_info=extra_info,
            )
        if isinstance(exception, (AccessError, AccessDenied)):
            extra_info = getattr(exception, "rest_json_info", None)
            return wrapJsonException(
                Forbidden(ustr(exception)),
                include_description=True,
                extra_info=extra_info,
            )
        if isinstance(exception, (UserError, ValidationError, ValueError)):
            extra_info = getattr(exception, "rest_json_info", None)
            return wrapJsonException(
                BadRequest(exception.args[0]),
                include_description=True,
                extra_info=extra_info,
            )
        if isinstance(exception, HTTPException):
            extra_info = getattr(exception, "rest_json_info", None)
            return wrapJsonException(
                exception, include_description=True, extra_info=extra_info
            )
        if isinstance(exception, Unauthorized):
            extra_info = getattr(exception, "rest_json_info", None)
            return (
                wrapJsonException(
                    exception, include_description=True, extra_info=extra_info
                ),
            )
        extra_info = getattr(exception, "rest_json_info", None)
        return wrapJsonException(InternalServerError(exception), extra_info=extra_info)
