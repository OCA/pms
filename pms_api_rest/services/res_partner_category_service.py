from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPartnerCategoriesService(Component):
    _inherit = "base.rest.service"
    _name = "res.partner.category.service"
    _usage = "categories"
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
        output_param=Datamodel("res.partner.category.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_categories(self):
        result_categories = []
        ResPartnerCategoryInfo = self.env.datamodels["res.partner.category.info"]
        for category in self.env["res.partner.category"].search([]):
            result_categories.append(
                ResPartnerCategoryInfo(
                    id=category.id,
                    name=category.name,
                    parentId=category.parent_id.id if category.parent_id.id else 0,
                )
            )
        return result_categories
