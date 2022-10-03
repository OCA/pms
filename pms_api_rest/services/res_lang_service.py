from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class ReslANGService(Component):
    _inherit = "base.rest.service"
    _name = "res.lang.service"
    _usage = "languages"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("res.lang.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partners(self):
        result_langs = []
        ResLangInfo = self.env.datamodels["res.lang.info"]
        languages = self.env["res.lang"].get_installed()
        for lang in languages:
            result_langs.append(
                ResLangInfo(
                    code=lang[0],
                    name=lang[1],
                )
            )
        return result_langs
