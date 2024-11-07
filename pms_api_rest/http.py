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
        super(RestApiDispatcherPms, self).__init__(httprequest)

    def handle_error(self, exception):
        """Called within an except block to allow converting exceptions
        to abitrary responses. Anything returned (except None) will
        be used as response."""
        if isinstance(exception, SessionExpiredException):
            # we don't want to return the login form as plain html page
            # we want to raise a proper exception
            return wrapJsonException(Unauthorized(ustr(exception)))
        try:
            return super(RestApiDispatcher, self)._handle_exception(exception)
        except MissingError as e:
            extra_info = getattr(e, "rest_json_info", None)
            return wrapJsonException(
                NotFound(ustr(e)), include_description=True, extra_info=extra_info
            )
        except (AccessError, AccessDenied) as e:
            extra_info = getattr(e, "rest_json_info", None)
            return wrapJsonException(
                Forbidden(ustr(e)), include_description=True, extra_info=extra_info
            )
        except (UserError, ValidationError, ValueError) as e:
            extra_info = getattr(e, "rest_json_info", None)
            return wrapJsonException(
                BadRequest(e.args[0]), include_description=True, extra_info=extra_info
            )
        except HTTPException as e:
            extra_info = getattr(e, "rest_json_info", None)
            return wrapJsonException(e, include_description=True, extra_info=extra_info)
        except Unauthorized as e:
            extra_info = getattr(e, "rest_json_info", None)
            return (
                wrapJsonException(e, include_description=True, extra_info=extra_info),
            )

        except Exception as e:  # flake8: noqa: E722
            extra_info = getattr(e, "rest_json_info", None)
            return wrapJsonException(InternalServerError(e), extra_info=extra_info)
