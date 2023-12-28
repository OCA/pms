from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPropertyService(Component):
    _inherit = "pms.property.service"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.property.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_properties(self):
        result_properties = super(PmsPropertyService, self).get_properties()
        for prop_info in result_properties:
            pms_property = self.env["pms.property"].browse(prop_info.id)
            prop_info.isUsedRegula = pms_property.is_used_regula
        return result_properties
