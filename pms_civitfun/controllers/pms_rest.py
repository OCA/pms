from odoo.addons.base_rest.controllers import main


class BaseRestCivitfunApiController(main.RestController):
    _root_path = "/civitfun/"
    _collection_name = "civitfun.services"
    _default_auth = "public"
    _default_save_session = False
    _default_cors = "*"
