from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAgencyService(Component):
    _inherit = "base.rest.service"
    _name = "pms.agency.service"
    _usage = "agencies"
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
        input_param=Datamodel("pms.agency.search.param"),
        output_param=Datamodel("pms.agency.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_agencies(self, agencies_search_param):
        domain = [("is_agency", "=", True)]
        if agencies_search_param.name:
            domain.append(("name", "like", agencies_search_param.name))
        result_agencies = []
        PmsAgencyInfo = self.env.datamodels["pms.agency.info"]
        for agency in self.env["res.partner"].search(
            domain,
        ):

            result_agencies.append(
                PmsAgencyInfo(
                    id=agency.id,
                    name=agency.name,
                )
            )
        return result_agencies

    @restapi.method(
        [
            (
                [
                    "/<int:agency_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.agency.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_agency(self, agency_id):
        agency = self.env["res.partner"].search(
            [
                ("id", "=", agency_id),
                ("is_agency", "=", True),
            ]
        )
        if agency:
            PmsAgencieInfo = self.env.datamodels["pms.agency.info"]
            return PmsAgencieInfo(
                id=agency.id,
                name=agency.name,
            )
        else:
            raise MissingError(_("Agency not found"))
