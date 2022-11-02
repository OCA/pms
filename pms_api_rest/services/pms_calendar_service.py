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
        date_from = datetime.strptime(calendar_search_param.dateFrom, "%Y-%m-%d").date()
        date_to = datetime.strptime(calendar_search_param.dateTo, "%Y-%m-%d").date()
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        pms_property_id = calendar_search_param.pmsPropertyId
        subselect_sum_services_price = "(" \
                                       " SELECT COALESCE(SUM(s.price_day_total),0) price_day_total_services " \
                                       " FROM pms_service_line s " \
                                       " WHERE s.reservation_id = night.reservation_id " \
                                       " AND s.date = night.date AND NOT s.is_board_service " \
                                       " ) "
        selected_fields_mapper = {
            "id": "night.id",
            "state": "night.state",
            "date": "DATE(night.date)",
            "room_id": "night.room_id",
            "room_type_name": "pms_room_type.default_code",
            "to_assign": "reservation.to_assign",
            "splitted": "reservation.splitted",
            "partner_id": "reservation.partner_id",
            "partner_name": "reservation.partner_name",
            "folio_id": "folio.id",
            "reservation_id": "reservation.id",
            "reservation_name": "reservation.name",
            "reservation_type": "reservation.reservation_type",
            "checkin": "reservation.checkin",
            "checkout": "reservation.checkout",
            "price_total": "reservation.price_total",
            "folio_pending_amount": "folio.pending_amount",
            "adults": "reservation.adults",
            "price_day_total": "night.price_day_total",
            "price_day_total_services": subselect_sum_services_price
        }
        selected_fields_sql = list(selected_fields_mapper.values())
        selected_fields = list(selected_fields_mapper.keys())
        sql_select = "SELECT %s" % ", ".join(selected_fields_sql)
        self.env.cr.execute(
            f"""
            {sql_select}
            FROM    pms_reservation_line  night
                    LEFT JOIN pms_reservation reservation
                        ON reservation.id = night.reservation_id
                    LEFT JOIN pms_room_type
                        ON pms_room_type.id = reservation.room_type_id
                    LEFT JOIN pms_folio folio
                        ON folio.id = reservation.folio_id
            WHERE   (night.pms_property_id = %s)
                AND (night.date in %s)
                AND (night.state != 'cancel')
            """,
            (
                pms_property_id,
                tuple(target_dates),
            ),
        )
        result_sql = self.env.cr.fetchall()
        lines = []
        for res in result_sql:
            lines.append(
                {field: res[selected_fields.index(field)] for field in selected_fields}
            )

        PmsCalendarInfo = self.env.datamodels["pms.calendar.info"]
        result_lines = []
        for line in lines:
            next_line_splitted = False
            previous_line_splitted = False
            is_first_night = line["checkin"] == line["date"]
            is_last_night = line["checkout"] + timedelta(days=-1) == line["date"]
            if line.get("splitted"):
                next_line = next(
                    (
                        item
                        for item in lines
                        if item["reservation_id"] == line["reservation_id"]
                        and item["date"] == line["date"] + timedelta(days=1)
                    ),
                    False,
                )
                if next_line:
                    next_line_splitted = next_line["room_id"] != line["room_id"]

                previous_line = next(
                    (
                        item
                        for item in lines
                        if item["reservation_id"] == line["reservation_id"]
                        and item["date"] == line["date"] + timedelta(days=-1)
                    ),
                    False,
                )
                if previous_line:
                    previous_line_splitted = previous_line["room_id"] != line["room_id"]
            result_lines.append(
                PmsCalendarInfo(
                    id=line["id"],
                    state=line["state"],
                    date=datetime.combine(
                        line["date"], datetime.min.time()
                    ).isoformat(),
                    roomId=line["room_id"],
                    roomTypeName=str(line["room_type_name"]),
                    toAssign=line["to_assign"],
                    splitted=line["splitted"],
                    partnerId=line["partner_id"] or None,
                    partnerName=line["partner_name"] or None,
                    folioId=line["folio_id"],
                    reservationId=line["reservation_id"],
                    reservationName=line["reservation_name"],
                    reservationType=line["reservation_type"],
                    isFirstNight=is_first_night,
                    isLastNight=is_last_night,
                    totalPrice=round(line["price_total"], 2),
                    pendingPayment=round(line["folio_pending_amount"], 2),
                    priceDayTotal=round(line["price_day_total"], 0),
                    priceDayTotalServices=round(line["price_day_total_services"], 0),
                    # TODO: line.reservation_id.message_needaction_counter is computed field,
                    numNotifications=0,
                    adults=line["adults"],
                    nextLineSplitted=next_line_splitted,
                    previousLineSplitted=previous_line_splitted,
                    hasNextLine=not is_last_night,  # REVIEW: redundant with isLastNight?
                    closureReason=line[
                        "partner_name"
                    ],  # REVIEW: is necesary closure_reason_id?
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
        reservation_lines_target = (
            self.env["pms.reservation.line"]
            .search([("id", "in", swap_info.reservationLineIds)])
            .sorted(key=lambda l: l.date)
        )

        for reservation_line in reservation_lines_target:
            old_room_id = reservation_line.room_id
            affected_line = self.env["pms.reservation.line"].search(
                [
                    ("date", "=", reservation_line.date),
                    ("room_id", "=", swap_info.roomId),
                ]
            )
            reservation_line.occupies_availability = False
            affected_line.occupies_availability = False

            reservation_line.flush()
            affected_line.flush()

            reservation_line.room_id = swap_info.roomId
            affected_line.room_id = old_room_id

            reservation_line.occupies_availability = True
            affected_line.occupies_availability = True

            reservation_line._compute_occupies_availability()
            affected_line._compute_occupies_availability()

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
        date_from = datetime.strptime(
            pms_calendar_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(pms_calendar_search_param.dateTo, "%Y-%m-%d").date()
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        pms_property_id = pms_calendar_search_param.pmsPropertyId

        self.env.cr.execute(
            """
            SELECT night.date, SUM(night.price_day_total) AS production
            FROM    pms_reservation_line  night
            WHERE   (night.pms_property_id = %s)
                AND (night.date in %s)
            GROUP BY night.date
            """,
            (
                pms_property_id,
                tuple(target_dates),
            ),
        )
        production_per_nights_date = self.env.cr.fetchall()

        self.env.cr.execute(
            """
            SELECT service.date, SUM(service.price_day_total) AS production
            FROM    pms_service_line service
            WHERE   (service.pms_property_id = %s)
                AND (service.date in %s)
            GROUP BY service.date
            """,
            (
                pms_property_id,
                tuple(target_dates),
            ),
        )
        production_per_services_date = self.env.cr.fetchall()

        production_per_nights_dict = [
            {"date": item[0], "total": item[1]} for item in production_per_nights_date
        ]
        production_per_services_dict = [
            {"date": item[0], "total": item[1]} for item in production_per_services_date
        ]

        result = []
        PmsCalendarDailyInvoicing = self.env.datamodels["pms.calendar.daily.invoicing"]
        for day in target_dates:
            night_production = next(
                (
                    item["total"]
                    for item in production_per_nights_dict
                    if item["date"] == day
                ),
                False,
            )
            service_production = next(
                (
                    item["total"]
                    for item in production_per_services_dict
                    if item["date"] == day
                ),
                False,
            )
            result.append(
                PmsCalendarDailyInvoicing(
                    date=datetime.combine(day, datetime.min.time()).isoformat(),
                    invoicingTotal=round(
                        (night_production or 0) + (service_production or 0), 2
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
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        pms_property_id = pms_calendar_search_param.pmsPropertyId

        self.env.cr.execute(
            """
            SELECT  night.date AS date, room.room_type_id AS room_type, COUNT(night.id) AS count
            FROM    pms_reservation_line  night
                    LEFT JOIN pms_room room
                        ON night.room_id = room.id
            WHERE   (night.pms_property_id = %s)
                AND (night.date in %s)
                AND (night.occupies_availability = True)
            GROUP BY night.date, room.room_type_id
            """,
            (
                pms_property_id,
                tuple(target_dates),
            ),
        )
        result_sql = self.env.cr.fetchall()
        rooms = self.env["pms.room"].search([("pms_property_id", "=", pms_property_id)])
        room_types = rooms.mapped("room_type_id")
        total_rooms_by_room_type = [
            {
                "room_type_id": room_type.id,
                "rooms_total": len(
                    self.env["pms.room"].search(
                        [
                            ("room_type_id", "=", room_type.id),
                            ("pms_property_id", "=", pms_property_id),
                        ]
                    )
                ),
            }
            for room_type in room_types
        ]
        PmsCalendarFreeDailyRoomsByType = self.env.datamodels[
            "pms.calendar.free.daily.rooms.by.type"
        ]
        result = []
        for day in target_dates:
            for total_room_type in total_rooms_by_room_type:
                count_occupied_night_by_room_type = next(
                    (
                        item[2]
                        for item in result_sql
                        if item[0] == day and item[1] == total_room_type["room_type_id"]
                    ),
                    0,
                )
                result.append(
                    PmsCalendarFreeDailyRoomsByType(
                        date=str(
                            datetime.combine(day, datetime.min.time()).isoformat()
                        ),
                        roomTypeId=total_room_type["room_type_id"],
                        freeRooms=total_room_type["rooms_total"]
                        - count_occupied_night_by_room_type,
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
        date_from = datetime.strptime(
            pms_calendar_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(pms_calendar_search_param.dateTo, "%Y-%m-%d").date()
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        pms_property_id = pms_calendar_search_param.pmsPropertyId

        self.env.cr.execute(
            """
            SELECT  night.date AS date, COUNT(night.id) AS count
            FROM    pms_reservation_line  night
            WHERE   (night.pms_property_id = %s)
                AND (night.date in %s)
                AND (night.overbooking = True)
            GROUP BY night.date
            """,
            (
                pms_property_id,
                tuple(target_dates),
            ),
        )
        result_sql = self.env.cr.fetchall()
        PmsCalendarAlertsPerDay = self.env.datamodels["pms.calendar.alerts.per.day"]
        result = []
        for day in target_dates:
            overbooking_lines = next((item for item in result_sql if item[0] == day), 0)
            result.append(
                PmsCalendarAlertsPerDay(
                    date=str(datetime.combine(day, datetime.min.time()).isoformat()),
                    overbooking=True if overbooking_lines > 0 else False,
                )
            )
        return result

    @restapi.method(
        [
            (
                [
                    "/p/<int:reservation_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.reservation.updates", is_list=False),
        auth="jwt_api_pms",
    )
    def update_reservation(self, reservation_id, reservation_lines_changes):
        if reservation_lines_changes.reservationLinesChanges:

            # TEMP: Disabled temporal date changes to avoid drag&drops errors
            lines_to_change = self.env["pms.reservation.line"].browse(
                [
                    item["reservationLineId"]
                    for item in reservation_lines_changes.reservationLinesChanges
                ]
            )
            lines_to_change.room_id = reservation_lines_changes.reservationLinesChanges[
                0
            ]["roomId"]
            # # get date of first reservation id to change
            # first_reservation_line_id_to_change = (
            #     reservation_lines_changes.reservationLinesChanges[0][
            #         "reservationLineId"
            #     ]
            # )
            # first_reservation_line_to_change = self.env["pms.reservation.line"].browse(
            #     first_reservation_line_id_to_change
            # )
            # date_first_reservation_line_to_change = datetime.strptime(
            #     reservation_lines_changes.reservationLinesChanges[0]["date"], "%Y-%m-%d"
            # )

            # # iterate changes
            # for change_iterator in sorted(
            #     reservation_lines_changes.reservationLinesChanges,
            #     # adjust order to start changing from last/first reservation line
            #     # to avoid reservation line date constraint
            #     reverse=first_reservation_line_to_change.date
            #     < date_first_reservation_line_to_change.date(),
            #     key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"),
            # ):
            #     # recordset of each line
            #     line_to_change = self.env["pms.reservation.line"].search(
            #         [
            #             ("reservation_id", "=", reservation_id),
            #             ("id", "=", change_iterator["reservationLineId"]),
            #         ]
            #     )
            #     # modifying date, room_id, ...
            #     if "date" in change_iterator:
            #         line_to_change.date = change_iterator["date"]
            #     if (
            #         "roomId" in change_iterator
            #         and line_to_change.room_id.id != change_iterator["roomId"]
            #     ):
            #         line_to_change.room_id = change_iterator["roomId"]

            # max_value = max(
            #     first_reservation_line_to_change.reservation_id.reservation_line_ids.mapped(
            #         "date"
            #     )
            # ) + timedelta(days=1)
            # min_value = min(
            #     first_reservation_line_to_change.reservation_id.reservation_line_ids.mapped(
            #         "date"
            #     )
            # )
            # reservation = self.env["pms.reservation"].browse(reservation_id)
            # reservation.checkin = min_value
            # reservation.checkout = max_value

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
