from datetime import datetime, timedelta

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsCalendarService(Component):
    _inherit = "base.rest.service"
    _name = "pms.private.services"
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
        domain.append(("date", ">=", calendar_search_param.date_from))
        domain.append(("date", "<=", calendar_search_param.date_to))
        domain.append(("pms_property_id", "=", calendar_search_param.pms_property_id))
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
                    reservationId=line.reservation_id,
                    reservationName=line.reservation_id.name,
                    reservationType=line.reservation_id.reservation_type,
                    isFirstNight=line.reservation_id.checkin == line.date,
                    isLastNight=line.reservation_id.checkout + timedelta(days=-1)
                    == line.date,
                    totalPrice=line.reservation_id.price_total,
                    pendingPayment=line.reservation_id.folio_pending_amount,
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
                ("pms_property_id", "=", swap_info.pms_property_id),
            ]
        )

        lines_room_b = self.env["pms.reservation.line"].search(
            [
                ("room_id", "=", room_id_b),
                ("date", ">=", swap_info.swapFrom),
                ("date", "<=", swap_info.swapTo),
                ("pms_property_id", "=", swap_info.pms_property_id),
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
                ("date", ">=", pms_calendar_search_param.date_from),
                ("date", "<=", pms_calendar_search_param.date_to),
                ("pms_property_id", "=", pms_calendar_search_param.pms_property_id),
            ]
        )
        service_lines = self.env["pms.service.line"].search(
            [
                ("date", ">=", pms_calendar_search_param.date_from),
                ("date", "<=", pms_calendar_search_param.date_to),
                ("pms_property_id", "=", pms_calendar_search_param.pms_property_id),
            ]
        )

        date_from = datetime.strptime(
            pms_calendar_search_param.date_from, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            pms_calendar_search_param.date_to, "%Y-%m-%d"
        ).date()

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
                    invoicingTotal=sum(reservation_lines_by_day.mapped("price"))
                    + sum(service_lines_by_day.mapped("price_day_total")),
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
            pms_calendar_search_param.date_from, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            pms_calendar_search_param.date_to, "%Y-%m-%d"
        ).date()
        result = []
        PmsCalendarFreeDailyRoomsByType = self.env.datamodels[
            "pms.calendar.free.daily.rooms.by.type"
        ]
        for date in (
            date_from + timedelta(d) for d in range((date_to - date_from).days + 1)
        ):
            rooms = self.env["pms.room"].search(
                [("pms_property_id", "=", pms_calendar_search_param.pms_property_id)]
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
                            pms_calendar_search_param.pms_property_id,
                        ),
                    ]
                )
                num_rooms_room_type = self.env["pms.room"].search_count(
                    [
                        (
                            "pms_property_id",
                            "=",
                            pms_calendar_search_param.pms_property_id,
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
            pms_calendar_search_param.date_from, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            pms_calendar_search_param.date_to, "%Y-%m-%d"
        ).date()
        result = []
        for day in (
            date_from + timedelta(d) for d in range((date_to - date_from).days + 1)
        ):
            overbooking = False
            reservations = self.env["pms.reservation"].search(
                [
                    ("checkin", "=", day),
                    ("pms_property_id", "=", pms_calendar_search_param.pms_property_id),
                ]
            )
            if any(reservation.overbooking for reservation in reservations):
                overbooking = True
            result.append(
                PmsCalendarAlertsPerDay(
                    date=str(datetime.combine(day, datetime.min.time()).isoformat()),
                    overbooking=overbooking,
                )
            )
        return result
