from odoo.addons.base_rest.controllers import main


class BaseRestPrivateApiController(main.RestController):
    _root_path = "/api/"
    _collection_name = "pms.services"
    _default_auth = "public"
    _default_save_session = False
    _default_cors = "*"
