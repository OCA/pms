from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPartnerService(Component):
    _inherit = "base.rest.service"
    _name = "pms.partner.service"
    _usage = "partners"
    _collection = "pms.reservation.service"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.partner.short.info", is_list=True),
        auth="public",
    )
    def get_partners(self):
        domain = []
        result_partners = []
        PmsPartnerShortInfo = self.env.datamodels["pms.partner.short.info"]
        for partner in (
            self.env["res.partner"]
            .sudo()
            .search(
                domain,
            )
        ):

            result_partners.append(
                PmsPartnerShortInfo(
                    id=partner.id,
                    name=partner.name,
                )
            )
        return result_partners
