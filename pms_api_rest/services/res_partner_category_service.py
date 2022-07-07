from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsIdCategoriesService(Component):
    _inherit = "base.rest.service"
    _name = "res.partner.category.services"
    _usage = "segmentations"
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
    def get_parent_segmentation_ids(self):
        result_segmentation_ids = []
        ResPartnerCategoryInfo = self.env.datamodels["res.partner.category.info"]
        for segmentation_id in self.env["res.partner.category"].search([]):
            result_segmentation_ids.append(
                ResPartnerCategoryInfo(
                    id=segmentation_id.id,
                    name=segmentation_id.name,
                    parentId=segmentation_id.parent_id.id
                    if segmentation_id.parent_id.id
                    else 0,
                )
            )
        return result_segmentation_ids
