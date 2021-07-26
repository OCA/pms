from odoo.addons.base_rest.controllers import main

from ..lib.jwt_http import jwt_http
from ..lib.validator import validator


class BaseRestDemoPublicApiController(main.RestController):
    _root_path = "/api/"
    _collection_name = "pms.reservation.service"
    _default_auth = "public"

    # RestController OVERRIDE method
    def _process_method(self, service_name, method_name, *args, params=None):

        http_method, body, headers, token = jwt_http.parse_request()
        result = validator.verify_token(token)
        if not result["status"]:
            return jwt_http.errcode(code=result["code"], message=result["message"])
        else:
            return super(BaseRestDemoPublicApiController, self)._process_method(
                service_name, method_name, *args, params=params
            )
