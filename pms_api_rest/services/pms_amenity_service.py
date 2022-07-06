from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAmenityService(Component):
    _inherit = "base.rest.service"
    _name = "pms.amenity.service"
    _usage = "amenities"
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
        input_param=Datamodel("pms.amenity.search.param"),
        output_param=Datamodel("pms.amenity.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_amenities(self, amenities_search_param):
        domain = [("pms_amenity_type_id", "!=", False)]
        if amenities_search_param.name:
            domain.append(("name", "like", amenities_search_param.name))
        if amenities_search_param.id:
            domain.append(("id", "=", amenities_search_param.id))
        if amenities_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    ("pms_property_ids", "in", amenities_search_param.pmsPropertyId),
                    ("pms_property_ids", "=", False),
                ]
            )

        result_amenities = []
        PmsAmenityInfo = self.env.datamodels["pms.amenity.info"]
        for amenity in self.env["pms.amenity"].search(
            domain,
        ):

            result_amenities.append(
                PmsAmenityInfo(
                    id=amenity.id,
                    name=amenity.name,
                    amenityTypeId=amenity.pms_amenity_type_id.id,
                )
            )
        return result_amenities

    @restapi.method(
        [
            (
                [
                    "/<int:amenity_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.amenity.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_amenity(self, amenity_id):
        amenity = self.env["pms.amenity"].search([("id", "=", amenity_id)])
        if amenity:
            PmsAmenityInfo = self.env.datamodels["pms.amenity.info"]
            return PmsAmenityInfo(
                id=amenity.id,
                name=amenity.name,
                defaultCode=amenity.default_code,
                pmsAmenityTypeId=amenity.pms_amenity_type_id.id,
            )
        else:
            raise MissingError(_("Amenity not found"))
