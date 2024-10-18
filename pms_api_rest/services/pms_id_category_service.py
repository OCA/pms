from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsIdCategoryService(Component):
    _inherit = "base.rest.service"
    _name = "pms.id.category.service"
    _usage = "id-categories"
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
        output_param=Datamodel("pms.id.category.info", is_list=True),
        auth="public",
    )
    def get_id_categories(self):
        result_id_categories = []
        PmsIdCategoryInfo = self.env.datamodels["pms.id.category.info"]
        for id_category in (
            self.env["res.partner.id_category"]
            .with_context(lang=self.env.user.lang)
            .sudo()
            .search([], order="priority asc")
        ):
            result_id_categories.append(
                PmsIdCategoryInfo(
                    id=id_category.id,
                    documentType=id_category.name,
                    code=id_category.code,
                    countryIds=id_category.country_ids.mapped("id"),
                )
            )
        return result_id_categories
