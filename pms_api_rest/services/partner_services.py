from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPartnerService(Component):
    _inherit = "base.rest.service"
    _name = "pms.partner.service"
    _usage = "partners"
    _collection = "pms.private.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.partner.info", is_list=True),
    )
    def get_partners(self):
        domain = []
        result_partners = []
        PmsPartnerInfo = self.env.datamodels["pms.partner.info"]
        for partner in (
            self.env["res.partner"]
            .sudo()
            .search(
                domain,
            )
        ):

            result_partners.append(
                PmsPartnerInfo(
                    id=partner.id,
                    name=partner.name,
                )
            )
        return result_partners
