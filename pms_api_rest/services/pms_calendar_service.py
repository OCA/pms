from datetime import datetime, timedelta

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsCalendarService(Component):
    _inherit = "base.rest.service"
    _name = "pms.private.service"
    _usage = "calendar"
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
        input_param=Datamodel("pms.calendar.search.param"),
        output_param=Datamodel("pms.calendar.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_calendar(self, calendar_search_param):
        domain = list()
        domain.append(("date", ">=", calendar_search_param.dateFrom))
        domain.append(("date", "<=", calendar_search_param.dateTo))
        domain.append(("pms_property_id", "=", calendar_search_param.pmsPropertyId))
        domain.append(("state", "!=", "cancel"))
        result_lines = []
        PmsCalendarInfo = self.env.datamodels["pms.calendar.info"]
        for line in self.env["pms.reservation.line"].search(
            domain,
        ):
            next_line_splitted = False
            next_line = self.env["pms.reservation.line"].search(
                [
                    ("reservation_id", "=", line.reservation_id.id),
                    ("date", "=", line.date + timedelta(days=1)),
                ]
            )
            if next_line:
                next_line_splitted = next_line.room_id != line.room_id

            previous_line_splitted = False
            previous_line = self.env["pms.reservation.line"].search(
                [
                    ("reservation_id", "=", line.reservation_id.id),
                    ("date", "=", line.date + timedelta(days=-1)),
                ]
            )
            if previous_line:
                previous_line_splitted = previous_line.room_id != line.room_id

            result_lines.append(
                PmsCalendarInfo(
                    id=line.id,
                    state=line.reservation_id.state,
                    date=datetime.combine(line.date, datetime.min.time()).isoformat(),
                    roomId=line.room_id.id,
                    roomTypeName=str(line.reservation_id.room_type_id.default_code),
                    toAssign=line.reservation_id.to_assign,
                    splitted=line.reservation_id.splitted,
                    partnerId=line.reservation_id.partner_id.id or None,
                    partnerName=line.reservation_id.partner_name or None,
                    folioId=line.reservation_id.folio_id,
                    reservationId=line.reservation_id,
                    reservationName=line.reservation_id.name,
                    reservationType=line.reservation_id.reservation_type,
                    isFirstNight=line.reservation_id.checkin == line.date,
                    isLastNight=line.reservation_id.checkout + timedelta(days=-1)
                    == line.date,
                    totalPrice=round(line.reservation_id.price_total, 2),
                    pendingPayment=round(line.reservation_id.folio_pending_amount, 2),
                    numNotifications=line.reservation_id.message_needaction_counter,
                    adults=line.reservation_id.adults,
                    nextLineSplitted=next_line_splitted,
                    previousLineSplitted=previous_line_splitted,
                    hasNextLine=bool(next_line),
                    closureReason=line.reservation_id.closure_reason_id.name
                    if line.reservation_id.closure_reason_id
                    else "",
                )
            )
        return result_lines

    @restapi.method(
        [
            (
                [
                    "/swap",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.calendar.swap.info", is_list=False),
        auth="jwt_api_pms",
    )
    def swap_reservation_slices(self, swap_info):
        room_id_a = swap_info.roomIdA
        room_id_b = swap_info.roomIdB

        lines_room_a = self.env["pms.reservation.line"].search(
            [
                ("room_id", "=", room_id_a),
                ("date", ">=", swap_info.swapFrom),
                ("date", "<=", swap_info.swapTo),
                ("pms_property_id", "=", swap_info.pmsPropertyId),
            ]
        )

        lines_room_b = self.env["pms.reservation.line"].search(
            [
                ("room_id", "=", room_id_b),
                ("date", ">=", swap_info.swapFrom),
                ("date", "<=", swap_info.swapTo),
                ("pms_property_id", "=", swap_info.pmsPropertyId),
            ]
        )
        lines_room_a.occupies_availability = False
        lines_room_b.occupies_availability = False
        lines_room_a.flush()
        lines_room_b.flush()
        lines_room_a.room_id = room_id_b
        lines_room_b.room_id = room_id_a

        lines_room_a._compute_occupies_availability()
        lines_room_b._compute_occupies_availability()

    @restapi.method(
        [
            (
                [
                    "/daily-invoicing",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.calendar.search.param", is_list=False),
        output_param=Datamodel("pms.calendar.daily.invoicing", is_list=True),
        auth="jwt_api_pms",
    )
    def get_daily_invoincing(self, pms_calendar_search_param):
        reservation_lines = self.env["pms.reservation.line"].search(
            [
                ("date", ">=", pms_calendar_search_param.dateFrom),
                ("date", "<=", pms_calendar_search_param.dateTo),
                ("pms_property_id", "=", pms_calendar_search_param.pmsPropertyId),
            ]
        )
        service_lines = self.env["pms.service.line"].search(
            [
                ("date", ">=", pms_calendar_search_param.dateFrom),
                ("date", "<=", pms_calendar_search_param.dateTo),
                ("pms_property_id", "=", pms_calendar_search_param.pmsPropertyId),
            ]
        )

        date_from = datetime.strptime(
            pms_calendar_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(pms_calendar_search_param.dateTo, "%Y-%m-%d").date()

        result = []
        PmsCalendarDailyInvoicing = self.env.datamodels["pms.calendar.daily.invoicing"]
        for day in (
            date_from + timedelta(d) for d in range((date_to - date_from).days + 1)
        ):
            reservation_lines_by_day = reservation_lines.filtered(
                lambda d: d.date == day
            )
            service_lines_by_day = service_lines.filtered(lambda d: d.date == day)
            result.append(
                PmsCalendarDailyInvoicing(
                    date=datetime.combine(day, datetime.min.time()).isoformat(),
                    invoicingTotal=round(
                        sum(reservation_lines_by_day.mapped("price"))
                        + sum(service_lines_by_day.mapped("price_day_total")),
                        2,
                    ),
                )
            )

        return result

    @restapi.method(
        [
            (
                [
                    "/free-rooms",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.calendar.search.param", is_list=False),
        output_param=Datamodel("pms.calendar.free.daily.rooms.by.type", is_list=True),
        auth="jwt_api_pms",
    )
    def get_free_rooms(self, pms_calendar_search_param):

        date_from = datetime.strptime(
            pms_calendar_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(pms_calendar_search_param.dateTo, "%Y-%m-%d").date()
        result = []
        PmsCalendarFreeDailyRoomsByType = self.env.datamodels[
            "pms.calendar.free.daily.rooms.by.type"
        ]
        for date in (
            date_from + timedelta(d) for d in range((date_to - date_from).days + 1)
        ):
            rooms = self.env["pms.room"].search(
                [("pms_property_id", "=", pms_calendar_search_param.pmsPropertyId)]
            )
            for room_type_iterator in self.env["pms.room.type"].search(
                [("id", "in", rooms.mapped("room_type_id").ids)]
            ):
                reservation_lines_room_type = self.env["pms.reservation.line"].search(
                    [
                        ("date", "=", date),
                        ("occupies_availability", "=", True),
                        ("room_id.room_type_id", "=", room_type_iterator.id),
                        (
                            "pms_property_id",
                            "=",
                            pms_calendar_search_param.pmsPropertyId,
                        ),
                    ]
                )
                num_rooms_room_type = self.env["pms.room"].search_count(
                    [
                        (
                            "pms_property_id",
                            "=",
                            pms_calendar_search_param.pmsPropertyId,
                        ),
                        ("room_type_id", "=", room_type_iterator.id),
                    ]
                )
                if not reservation_lines_room_type:
                    free_rooms_room_type = num_rooms_room_type
                else:
                    free_rooms_room_type = num_rooms_room_type - len(
                        reservation_lines_room_type
                    )
                result.append(
                    PmsCalendarFreeDailyRoomsByType(
                        date=str(
                            datetime.combine(date, datetime.min.time()).isoformat()
                        ),
                        roomTypeId=room_type_iterator.id,
                        freeRooms=free_rooms_room_type,
                    )
                )
        return result

    @restapi.method(
        [
            (
                [
                    "/alerts-per-day",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.calendar.search.param", is_list=False),
        output_param=Datamodel("pms.calendar.alerts.per.day", is_list=True),
        auth="jwt_api_pms",
    )
    def get_alerts_per_day(self, pms_calendar_search_param):
        PmsCalendarAlertsPerDay = self.env.datamodels["pms.calendar.alerts.per.day"]
        date_from = datetime.strptime(
            pms_calendar_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(pms_calendar_search_param.dateTo, "%Y-%m-%d").date()
        result = []
        for day in (
            date_from + timedelta(d) for d in range((date_to - date_from).days + 1)
        ):
            lines = self.env["pms.reservation.line"].search_count(
                [
                    ("date", "=", day),
                    ("pms_property_id", "=", pms_calendar_search_param.pmsPropertyId),
                    ("overbooking", "=", True),
                ]
            )
            result.append(
                PmsCalendarAlertsPerDay(
                    date=str(datetime.combine(day, datetime.min.time()).isoformat()),
                    overbooking=True if lines > 0 else False,
                )
            )
        return result

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.reservation.updates", is_list=False),
        auth="jwt_api_pms",
    )
    def update_reservation(self, reservation_id, reservation_lines_changes):
        if reservation_lines_changes.reservationLinesChanges:

            # get date of first reservation id to change
            first_reservation_line_id_to_change = (
                reservation_lines_changes.reservationLinesChanges[0][
                    "reservationLineId"
                ]
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

            max_value = max(
                first_reservation_line_to_change.reservation_id.reservation_line_ids.mapped(
                    "date"
                )
            ) + timedelta(days=1)
            min_value = min(
                first_reservation_line_to_change.reservation_id.reservation_line_ids.mapped(
                    "date"
                )
            )
            reservation = self.env["pms.reservation"].browse(reservation_id)
            reservation.checkin = min_value
            reservation.checkout = max_value

        else:
            reservation_to_update = (
                self.env["pms.reservation"].sudo().search([("id", "=", reservation_id)])
            )
            reservation_vals = {}

            if reservation_lines_changes.preferredRoomId:
                reservation_vals.update(
                    {"preferred_room_id": reservation_lines_changes.preferredRoomId}
                )
            if reservation_lines_changes.boardServiceId:
                reservation_vals.update(
                    {"board_service_room_id": reservation_lines_changes.boardServiceId}
                )
            if reservation_lines_changes.pricelistId:
                reservation_vals.update(
                    {"pricelist_id": reservation_lines_changes.pricelistId}
                )
            if reservation_lines_changes.adults:
                reservation_vals.update({"adults": reservation_lines_changes.adults})
            if reservation_lines_changes.children:
                reservation_vals.update(
                    {"children": reservation_lines_changes.children}
                )
            if reservation_lines_changes.segmentationId:
                reservation_vals.update(
                    {
                        "segmentation_ids": [
                            (6, 0, [reservation_lines_changes.segmentationId])
                        ]
                    }
                )
            reservation_to_update.write(reservation_vals)
