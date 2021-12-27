from odoo.addons.base_rest.controllers import main


class BaseRestPrivateApiController(main.RestController):
    _root_path = "/api/"
    _collection_name = "pms.private.services"
    _default_auth = "jwt_api_pms"
    _default_cors = "*"


class BaseRestPublicApiController(main.RestController):
    _root_path = "/auth/"
    _collection_name = "pms.public.services"
    _default_auth = "public"
    _default_cors = "*"
