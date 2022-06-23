from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsIdCategoriesService(Component):
    _inherit = "base.rest.service"
    _name = "pms.id.categories.services"
    _usage = "id_categories"
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
        output_param=Datamodel("pms.id.categories.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_id_categories(self):
        result_id_categories = []
        PmsIdCategoriesInfo = self.env.datamodels["pms.id.categories.info"]
        for id_category in self.env["res.partner.id_category"].search([]):
            result_id_categories.append(
                PmsIdCategoriesInfo(
                    id=id_category.id,
                    documentType=id_category.name,
                )
            )
        return result_id_categories
