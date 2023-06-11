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
        output_param=Datamodel("pms.calendar.render.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_calendar(self, calendar_search_param):
        """
        Optimized query to get calendar, with the next schema:
        [
        {
            "roomId":INT,
            "roomTypeId":INT,
            "dates":[
                {
                    "date":"2023-06-25T00:00:00",
                    "reservationLines":[
                    {
                        "folioId":INT,
                        "id":INT,
                        "reservationName":"203/23/000105/1",
                        "isFirstNight":false,
                        "pendingPayment":0,
                        "partnerId":null,
                        "numNotifications":0,
                        "priceDayTotalServices":0,
                        "partnerName":null,
                        "isLastNight":false,
                        "splitted":false,
                        "date":"2023-06-25T00:00:00",
                        "adults":0,
                        "nextLineSplitted":false,
                        "toAssign":false,
                        "totalPrice":0,
                        "state":"arrival_delayed",
                        "previous_itemSplitted":false,
                        "reservationId":466936,
                        "priceDayTotal":0,
                        "roomTypeName":"EST",
                        "roomId":1913,
                        "closureReasonId":1,
                        "reservationType":"out"
                    },
                    ...
                    ]
                },
                ...
            ]
        },
        ...
        ]
        """
        date_from = datetime.strptime(calendar_search_param.dateFrom, "%Y-%m-%d").date()
        date_to = datetime.strptime(calendar_search_param.dateTo, "%Y-%m-%d").date()
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        pms_property_id = calendar_search_param.pmsPropertyId
        # group by room_id, date and take account the first line for
        # reservation to build de reservationLines
        # array only in the first line
        selected_fields_mapper = {
            "id": "night.id as id",
            "state": "night.state as state",
            "date": "DATE(night.date) as date",
            "room_id": "night.room_id as room_id",
            "room_type_name": "pms_room_type.default_code as room_type_name",
            "to_assign": "reservation.to_assign as to_assign",
            "splitted": "reservation.splitted as splitted",
            "partner_id": "reservation.partner_id as partner_id",
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
            "closure_reason_id": "folio.closure_reason_id",
            "is_reselling": "reservation.is_reselling",
            # "price_day_total_services": subselect_sum_services_price,
        }
        selected_fields_sql = list(selected_fields_mapper.values())
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
                AND (night.occupies_availability = True)
            ORDER BY night.room_id, night.date
            """,
            (
                pms_property_id,
                tuple(target_dates),
            ),
        )
        result = self.env.cr.dictfetchall()
        response = []
        CalendarRenderInfo = self.env.datamodels["pms.calendar.render.info"]
        last_date = date_from - timedelta(days=1)
        for index, item in enumerate(result):
            last_reservation_id = (
                result[index - 1]["reservation_id"] if index > 0 else False
            )
            last_room_id = result[index - 1]["room_id"] if index > 0 else False
            # If the room_id is different from the previous one, we create a new
            # room object
            if item["room_id"] != last_room_id:
                response.append(
                    CalendarRenderInfo(
                        roomId=item["room_id"],
                        roomTypeId=item["room_type_name"],
                        dates=[],
                    )
                )
                # We use index_date to know the index of the
                # last date added with reservationLines
                # the index is avoid to use because we need
                # to add dates without reservationLines
                index_date = 0
            # If the date is the next one, and is the same reservation, we add
            # the reservation line to the last date and add avoid date in main array
            if (
                item["date"] == last_date + timedelta(days=1)
                and item["reservation_id"] == last_reservation_id
            ):
                response[-1].dates[index_date]["reservationLines"].append(
                    self._build_reservation_line(item)
                )
                response[-1].dates.append(
                    {
                        "date": datetime.combine(
                            item["date"], datetime.min.time()
                        ).isoformat(),
                        "reservationLines": [],
                    }
                )
                last_date = item["date"]
            # If the date not is the next one, we create a new date object
            # withouth reservation lines
            elif item["date"] != last_date + timedelta(days=1):
                response[-1].dates.extend(
                    self._build_dates_without_reservation_lines(
                        date_from=last_date + timedelta(days=1),
                        date_to=item["date"] - timedelta(days=1),
                    )
                )
                response[-1].dates.append(
                    {
                        "date": datetime.combine(
                            item["date"], datetime.min.time()
                        ).isoformat(),
                        "reservationLines": [
                            self._build_reservation_line(
                                item=item,
                                next_item=False
                                if not item["splitted"]
                                else result[index + 1],
                                previous_item=False
                                if not item["splitted"]
                                else result[index - 1],
                            )
                        ],
                    }
                )
                last_date = item["date"]
                index_date = len(response[-1].dates) - 1
            # else, the date is the next one, but the reservation is different
            # so we create a new date object with the reservation line
            else:
                response[-1].dates.append(
                    {
                        "date": datetime.combine(
                            item["date"], datetime.min.time()
                        ).isoformat(),
                        "reservationLines": [
                            self._build_reservation_line(
                                item=item,
                                next_item=False
                                if (not item["splitted"] or item["date"] == date_to)
                                else result[index + 1],
                                previous_item=False
                                if (not item["splitted"] or item["date"] == date_from)
                                else result[index - 1],
                            )
                        ],
                    }
                )
                last_date = item["date"]
                index_date = len(response[-1].dates) - 1
        return response

    def _build_dates_without_reservation_lines(self, date_from, date_to):
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        return [
            {
                "date": datetime.combine(date, datetime.min.time()).isoformat(),
                "reservationLines": [],
            }
            for date in target_dates
        ]

    def _build_reservation_line(self, item, next_item=False, previous_item=False):
        # next_item is sent if the current item is splitted
        # and the date not is the last in the range
        # (because in the last date, the reservation line no is
        # show with the next date splitted)
        # the same for previous_item
        next_itemSplitted = (
            item["splitted"]
            and next_item
            and item["date"] < item["checkout"] - timedelta(days=1)
            and (
                next_item["room_id"] != item["room_id"]
                or next_item["reservation_id"] != item["reservation_id"]
            )
        )
        previous_itemSplitted = (
            item["splitted"]
            and previous_item
            and item["date"] > item["checkin"] + timedelta(days=1)
            and (
                previous_item["room_id"] != item["room_id"]
                or previous_item["reservation_id"] != item["reservation_id"]
            )
        )
        return {
            "id": item["id"],
            "state": item["state"],
            "date": datetime.combine(item["date"], datetime.min.time()).isoformat(),
            "roomId": item["room_id"],
            "roomTypeName": item["room_type_name"],
            "toAssign": item["to_assign"],
            "splitted": item["splitted"],
            "partnerId": item["partner_id"],
            "partnerName": item["partner_name"],
            "folioId": item["folio_id"],
            "reservationId": item["reservation_id"],
            "reservationName": item["reservation_name"],
            "reservationType": item["reservation_type"],
            "adults": item["adults"],
            "priceDayTotal": item["price_day_total"],
            "closureReasonId": item["closure_reason_id"],
            "isFirstNight": item["date"] == item["checkin"],
            "isLastNight": item["date"] == item["checkout"] - timedelta(days=1),
            "totalPrice": item["price_total"],
            "pendingPayment": item["folio_pending_amount"],
            "numNotifications": 0,
            "nextLineSplitted": next_itemSplitted,
            "previous_itemSplitted": previous_itemSplitted,
            "priceDayTotalServices": 0,
            "isReselling": item["is_reselling"],
        }

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
            reservation_line.with_context(
                avoid_availability_check=True
            ).room_id = swap_info.roomId
            affected_line.with_context(
                avoid_availability_check=True
            ).room_id = old_room_id

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
                    self.env["pms.room"]
                    .with_context(active_test=True)
                    .search(
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
            overbooking_lines = next(
                (item[1] for item in result_sql if item[0] == day), 0
            )
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
            if reservation_lines_changes.boardServiceId is not None:
                reservation_vals.update(
                    {"board_service_room_id": reservation_lines_changes.boardServiceId}
                )
            if reservation_lines_changes.pricelistId:
                reservation_vals.update(
                    {"pricelist_id": reservation_lines_changes.pricelistId}
                )
            if reservation_lines_changes.adults:
                reservation_vals.update({"adults": reservation_lines_changes.adults})
            if reservation_lines_changes.children is not None:
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
