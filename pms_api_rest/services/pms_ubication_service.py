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
        ubication_all_properties = self.env["pms.ubication"].search(
            [("pms_property_ids", "=", False)]
        )
        if ubication_search_param.pmsPropertyIds:
            ubication = set()
            for index, prop in enumerate(ubication_search_param.pmsPropertyIds):
                ubication_with_query_property = self.env["pms.ubication"].search(
                    [("pms_property_ids", "=", prop)]
                )
                if index == 0:
                    ubication = set(ubication_with_query_property.ids)
                else:
                    ubication = ubication.intersection(
                        set(ubication_with_query_property.ids)
                    )
            ubication_total = list(set(list(ubication) + ubication_all_properties.ids))
        else:
            ubication_total = list(ubication_all_properties.ids)
        domain = [
            ("id", "in", ubication_total),
        ]

        result_ubications = []
        PmsUbicationInfo = self.env.datamodels["pms.ubication.info"]
        for ubication in self.env["pms.ubication"].search(
            domain,
        ):

            result_ubications.append(
                PmsUbicationInfo(
                    id=ubication.id,
                    name=ubication.name,
                    pmsPropertyIds=ubication.pms_property_ids.mapped("id"),
                )
            )
        return result_ubications
