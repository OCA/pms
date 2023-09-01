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
                    "/reservations",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.pending.reservations.search.param"),
        output_param=Datamodel("pms.dashboard.pending.reservations", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservations(self, pms_reservations_search_param):
        date_from = fields.Date.from_string(pms_reservations_search_param.dateFrom)
        date_to = fields.Date.from_string(pms_reservations_search_param.dateTo)

        domain = [
            ("checkin", ">=", date_from),
            ("checkin", "<=", date_to),
            ("state", "!=", "cancel"),
            ("reservation_type", "!=", "out")
        ]
        reservations = self.env["pms.reservation"].search(domain)
        PmsDashboardPendingReservations = self.env.datamodels["pms.dashboard.pending.reservations"]
        result = []
        for reservation in reservations:
            result.append(
                PmsDashboardPendingReservations(
                    id=reservation.id,
                    state=reservation.state,
                    checkin=datetime.combine(
                        reservation.checkin, datetime.min.time()
                    ).isoformat(),
                    reservationType=reservation.reservation_type,
                )
            )
        return result
