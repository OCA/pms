from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsRoomService(Component):
    _inherit = "base.rest.service"
    _name = "pms.reservation.service"
    _usage = "reservations"
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
        output_param=Datamodel("pms.reservation.info", is_list=True),
        auth="public",
    )
    def get_reservations(self):
        domain = []

        result_reservations = []
        PmsReservationInfo = self.env.datamodels["pms.reservation..info"]
        for reservation in (
            self.env["pms.reservation"]
            .sudo()
            .search(
                domain,
            )
        ):
            result_reservations.append(
                PmsReservationInfo(
                    id=reservation.id,
                    price=reservation.price_subtotal,
                    checkin=datetime.combine(reservation.checkin, datetime.min.time()).isoformat(),
                    checkout=datetime.combine(reservation.checkout, datetime.min.time()).isoformat(),
                )
            )
        return result_reservations
