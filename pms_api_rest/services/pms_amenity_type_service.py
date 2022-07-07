from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAmenityTypeService(Component):
    _inherit = "base.rest.service"
    _name = "pms.amenity.type.service"
    _usage = "amenity-types"
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
        input_param=Datamodel("pms.amenity.type.search.param"),
        output_param=Datamodel("pms.amenity.type.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_amenity_types(self, amenity_types_search_param):
        domain = []
        if amenity_types_search_param.name:
            domain.append(("name", "like", amenity_types_search_param.name))
        if amenity_types_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    (
                        "pms_property_ids",
                        "in",
                        amenity_types_search_param.pmsPropertyId,
                    ),
                    ("pms_property_ids", "=", False),
                ]
            )

        result_amenity_types = []
        PmsAmenityTypeInfo = self.env.datamodels["pms.amenity.type.info"]
        for amenity_type in self.env["pms.amenity.type"].search(
            domain,
        ):

            result_amenity_types.append(
                PmsAmenityTypeInfo(
                    id=amenity_type.id,
                    name=amenity_type.name,
                )
            )
        return result_amenity_types

    @restapi.method(
        [
            (
                [
                    "/<int:amenity_type_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.amenity.type.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_amenity_type(self, amenity_type_id):
        amenity_type = self.env["pms.amenity.type"].search(
            [("id", "=", amenity_type_id)]
        )
        if amenity_type:
            PmsAmenityTypeInfo = self.env.datamodels["pms.amenity.type.info"]
            return PmsAmenityTypeInfo(
                id=amenity_type.id,
                name=amenity_type.name,
            )
        else:
            raise MissingError(_("Amenity Type not found"))
