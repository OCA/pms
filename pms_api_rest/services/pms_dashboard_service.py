from odoo.addons.component.core import Component
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo import fields
from datetime import datetime



class PmsDashboardServices(Component):
    _inherit = "base.rest.service"
    _name = "pms.dashboard.service"
    _usage = "dashboard"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/checkins",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.checkins.search.param"),
        output_param=Datamodel("pms.dashboard.checkins", is_list=True),
        auth="jwt_api_pms",
    )
    def get_checkins(self, pms_checkins_search_param):
        date_from = fields.Date.from_string(pms_checkins_search_param.dateFrom)
        date_to = fields.Date.from_string(pms_checkins_search_param.dateTo)

        domain = [
            ("checkin", ">=", date_from),
            ("checkin", "<=", date_to),
            ("state", "in", ("confirm", "arrival_delayed")),
            ("reservation_type", "!=", "out")
        ]
        reservations = self.env["pms.reservation"].search(domain)
        PmsDashboardCheckins = self.env.datamodels["pms.dashboard.checkins"]
        result_checkins = []
        for checkin_partner in reservations.checkin_partner_ids:
            result_checkins.append(
                PmsDashboardCheckins(
                    id=checkin_partner.id,
                    checkinPartnerState=checkin_partner.state,
                    date=datetime.combine(
                        checkin_partner.checkin, datetime.min.time()
                    ).isoformat(),
                )
            )
        return result_checkins
