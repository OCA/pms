from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    NotFound,
    Unauthorized,
)

import odoo
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import HttpRequest, Root, SessionExpiredException
from odoo.loglevels import ustr

from odoo.addons.base_rest.http import (
    HttpRestRequest,
    _rest_services_routes,
    wrapJsonException,
)


class HttpRestRequestPms(HttpRestRequest):
    def __init__(self, httprequest):
        super(HttpRestRequestPms, self).__init__(httprequest)

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
    db = httprequest.session.db
    if db and odoo.service.db.exp_db_exist(db):
        # on the very first request processed by a worker,
        # registry is not loaded yet
        # so we enforce its loading here to make sure that
        # _rest_services_databases is not empty
        odoo.registry(db)
        rest_routes = _rest_services_routes.get(db, [])
        for root_path in rest_routes:
            if httprequest.path.startswith(root_path):
                return HttpRestRequestPms(httprequest)
    return ori_get_request(self, httprequest)


Root.get_request = get_request
