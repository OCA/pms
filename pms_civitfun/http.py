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
from odoo.http import HttpRequest, Root, SessionExpiredException
from odoo.loglevels import ustr

from odoo.addons.base_rest.http import HttpRestRequest, wrapJsonException


class HttpRestRequestCivitfun(HttpRestRequest):
    def __init__(self, httprequest):
        super(HttpRestRequestCivitfun, self).__init__(httprequest)

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
        to abitrary responses. Anything returned (except None) will
        be used as response."""
        if isinstance(exception, SessionExpiredException):
            # we don't want to return the login form as plain html page
            # we want to raise a proper exception
            return wrapJsonException(Unauthorized(ustr(exception)))
        try:
            return super(HttpRequest, self)._handle_exception(exception)
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
        except (UserError, ValidationError) as e:
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


ori_get_request = Root.get_request


def get_request(self, httprequest):
    if "civitfun" in httprequest.path:
        if (
            "HTTP_CIVITFUN_STANDARD3_REQUEST" in httprequest.environ
            and httprequest.environ.get("Civitfun-Standard3-Request") == "authorization"
        ):
            httprequest.environ["HTTP_AUTHORIZATION"] = httprequest.environ[
                "Civitfun-Standard3-Request"
            ]
        if (
            "CONTENT_TYPE" in httprequest.environ
            and httprequest.environ.get("CONTENT_TYPE") == "application/json"
            and not len(httprequest.get_data().decode(httprequest.charset)) > 0
        ):
            httprequest.environ["CONTENT_TYPE"] = "application/json-civitfun"
        return HttpRestRequestCivitfun(httprequest)
    return ori_get_request(self, httprequest)


Root.get_request = get_request
