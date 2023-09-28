from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsUbicationService(Component):
    _inherit = "base.rest.service"
    _name = "pms.ubication.service"
    _usage = "ubications"
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
        input_param=Datamodel("pms.ubication.search.param"),
        output_param=Datamodel("pms.ubication.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_ubications(self, ubication_search_param):
        if ubication_search_param.pmsPropertyIds:
            ubications = (
                self.env["pms.room"]
                .search(
                    [("pms_property_id", "in", ubication_search_param.pmsPropertyIds)]
                )
                .mapped("ubication_id")
            )
        else:
            ubications = self.env["pms.ubication"].search(
                [("pms_property_ids", "=", False)]
            )

        result_ubications = []
        PmsUbicationInfo = self.env.datamodels["pms.ubication.info"]
        for ubication in ubications:

            result_ubications.append(
                PmsUbicationInfo(
                    id=ubication.id,
                    name=ubication.name,
                    pmsPropertyIds=ubication.pms_property_ids.mapped("id"),
                )
            )
        return result_ubications
