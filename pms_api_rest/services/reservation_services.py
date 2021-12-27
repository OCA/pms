from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsRoomService(Component):
    _inherit = "base.rest.service"
    _name = "pms.reservation.service"
    _usage = "reservations"
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
        output_param=Datamodel("pms.reservation.info", is_list=True),
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

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.calendar.changes", is_list=False),
    )
    def move_reservation_line(self, reservation_id, reservation_lines_changes):

        # get date of first reservation id to change
        first_reservation_line_id_to_change = (
            reservation_lines_changes.reservationLinesChanges[0]["reservationLineId"]
        )
        first_reservation_line_to_change = self.env["pms.reservation.line"].browse(
            first_reservation_line_id_to_change
        )
        date_first_reservation_line_to_change = datetime.strptime(
            reservation_lines_changes.reservationLinesChanges[0]["date"], "%Y-%m-%d"
        )

        # iterate changes
        for change_iterator in sorted(
            reservation_lines_changes.reservationLinesChanges,
            # adjust order to start changing from last/first reservation line
            # to avoid reservation line date constraint
            reverse=first_reservation_line_to_change.date
            < date_first_reservation_line_to_change.date(),
            key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"),
        ):
            # recordset of each line
            line_to_change = self.env["pms.reservation.line"].search(
                [
                    ("reservation_id", "=", reservation_id),
                    ("id", "=", change_iterator["reservationLineId"]),
                ]
            )
            # modifying date, room_id, ...
            if "date" in change_iterator:
                line_to_change.date = change_iterator["date"]
            if (
                "roomId" in change_iterator
                and line_to_change.room_id.id != change_iterator["roomId"]
            ):
                line_to_change.room_id = change_iterator["roomId"]
