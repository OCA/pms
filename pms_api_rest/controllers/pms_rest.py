from odoo.addons.base_rest.controllers import main


class BaseRestDemoPublicApiController(main.RestController):
    _root_path = "/api/"
    _collection_name = "pms.reservation.service"
    _default_auth = "jwt_api_pms"
