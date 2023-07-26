from datetime import datetime, timedelta

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


def build_reservation_line_info( calendar_item, previous_item=False, next_item=False):
    next_itemSplitted = (
        calendar_item["splitted"]
        and next_item
        and calendar_item["date"] < calendar_item["checkout"] - timedelta(days=1)
        and (
            next_item["room_id"] != calendar_item["room_id"]
            or next_item["reservation_id"] != calendar_item["reservation_id"]
        )
    )
    previous_itemSplitted = (
        calendar_item["splitted"]
        and previous_item
        and calendar_item["date"] > calendar_item["checkin"]
        and (
            previous_item["room_id"] != calendar_item["room_id"]
            or previous_item["reservation_id"] != calendar_item["reservation_id"]
        )
    )
    return {
        "date": datetime.combine(calendar_item['date'], datetime.min.time()).isoformat(),
        "roomId": calendar_item['room_id'],
        "roomTypeId": calendar_item['room_type_id'],
        "id": calendar_item['id'],
        "state": calendar_item['state'],
        "priceDayTotal": calendar_item['price_day_total'],
        "toAssign": calendar_item['to_assign'],
        "splitted": calendar_item['splitted'],
        "partnerId": calendar_item['partner_id'],
        "partnerName": calendar_item['partner_name'],
        "folioId": calendar_item['folio_id'],
        "reservationId": calendar_item['reservation_id'],
        "reservationName": calendar_item['reservation_name'],
        "reservationType": calendar_item['reservation_type'],
        "checkin": datetime.combine(calendar_item['checkin'], datetime.min.time()).isoformat(),
        "checkout": datetime.combine(calendar_item['checkout'], datetime.min.time()).isoformat(),
        "priceTotal": calendar_item['price_total'],
        "adults": calendar_item['adults'],
        "pendingPayment": calendar_item['folio_pending_amount'],
        "closureReasonId": calendar_item['closure_reason_id'],
        "isFirstNight": calendar_item['date'] == calendar_item['checkin'] if calendar_item['checkin'] else None,
        "isLastNight": calendar_item['date'] == calendar_item['checkout'] + timedelta(days=-1)
        if calendar_item['checkout'] else None,
        "nextLineSplitted": next_itemSplitted,
        "previousLineSplitted": previous_itemSplitted,
    }


def build_restriction(item):
    result = {}
    if item['closed'] is not None and item['closed']:
        result.update({'closed': True})
    if item['closed_arrival'] is not None and item['closed_arrival']:
        result.update({'closedArrival': True})
    if item['closed_departure'] is not None and item['closed_departure']:
        result.update({'closedDeparture': True})
    if item['min_stay'] is not None and item['min_stay'] != 0:
        result.update({'minStay': item['min_stay']})
    if item['max_stay'] is not None and item['max_stay'] != 0:
        result.update({'maxStay': item['max_stay']})
    if item['min_stay_arrival'] is not None and item['min_stay_arrival'] != 0:
        result.update({'minStayArrival': item['min_stay_arrival']})
    if item['max_stay_arrival'] is not None and item['max_stay_arrival'] != 0:
        result.update({'maxStayArrival': item['max_stay_arrival']})
    return result


class PmsCalendarService(Component):
    _inherit = "base.rest.service"
    _name = "pms.private.service"
    _usage = "calendar"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/old-calendar",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.calendar.search.param"),
        output_param=Datamodel("pms.calendar.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_old_reservations_calendar(self, calendar_search_param):
        date_from = datetime.strptime(calendar_search_param.dateFrom, "%Y-%m-%d").date()
        date_to = datetime.strptime(calendar_search_param.dateTo, "%Y-%m-%d").date()
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        pms_property_id = calendar_search_param.pmsPropertyId

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
            "closure_reason_id": "folio.closure_reason_id",
            "is_reselling": "reservation.is_reselling",
            # "price_day_total_services": subselect_sum_services_price,
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
                    AND (night.occupies_availability = True)
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
                    priceDayTotalServices=0,
                    numNotifications=0,
                    adults=line["adults"],
                    nextLineSplitted=next_line_splitted,
                    previousLineSplitted=previous_line_splitted,
                    closureReasonId=line["closure_reason_id"],
                    isReselling=line["is_reselling"] if line["is_reselling"] else False,
                )
            )
        return result_lines

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
    def get_reservations_calendar(self, calendar_search_param):
        response = []
        date_from = datetime.strptime(calendar_search_param.dateFrom, "%Y-%m-%d").date()
        date_to = datetime.strptime(calendar_search_param.dateTo, "%Y-%m-%d").date()
        selected_fields_mapper = {
            "date": "dr.date date",
            "room_id": "dr.room_id room_id",
            "capacity": "dr.capacity capacity",
            "room_type_id": "dr.room_type_id room_type_id",
            "room_type_class_id": "dr.room_type_class_id room_type_class_id",
            "id": "l.id id",
            "state": "l.state state",
            "price_day_total": "l.price_day_total price_day_total",
            "to_assign": "r.to_assign to_assign",
            "splitted": "r.splitted splitted",
            "partner_id": "r.partner_id partner_id",
            "partner_name": "r.partner_name partner_name",
            "folio_id": "r.folio_id folio_id",
            "reservation_id": "r.id reservation_id",
            "reservation_name": "r.name reservation_name",
            "reservation_type": "r.reservation_type reservation_type",
            "checkin": "r.checkin checkin",
            "checkout": "r.checkout checkout",
            "price_total": "r.price_total price_total",
            "adults": "r.adults adults",
            "folio_pending_amount": "f.pending_amount folio_pending_amount",
            "closure_reason_id": "f.closure_reason_id closure_reason_id",
            "closed": "ru.closed closed",
            "closed_departure": "ru.closed_departure closed_departure",
            "closed_arrival": "ru.closed_arrival closed_arrival",
            "min_stay": "ru.min_stay min_stay",
            "min_stay_arrival": "ru.min_stay_arrival min_stay_arrival",
            "max_stay": "ru.max_stay max_stay",
            "max_stay_arrival": "ru.max_stay_arrival max_stay_arrival",
        }
        selected_fields_sql = list(selected_fields_mapper.values())
        sql_select = "SELECT %s" % ", ".join(selected_fields_sql)
        self.env.cr.execute(
            f"""
                {sql_select}
                FROM
                    (SELECT dates.date,
                            r_rt_rtc.room_id,
                            r_rt_rtc.capacity,
                            r_rt_rtc.room_type_id,
                            r_rt_rtc.room_type_class_id,
                            r_rt_rtc.sequence
                     FROM (SELECT (CURRENT_DATE + date ) date
                           FROM generate_series(date %s- CURRENT_DATE, date %s - CURRENT_DATE) date
                     ) dates,
                    (SELECT r.id room_id, r.capacity, rt.id room_type_id, rtc.id room_type_class_id,
                    r.sequence
                    FROM pms_room r
                    INNER JOIN pms_room_type rt ON rt.id = r.room_type_id
                    INNER JOIN pms_room_type_class rtc ON rtc.id = rt.class_id
                    WHERE r.active = true AND r.pms_property_id = %s) r_rt_rtc
                    ) dr
                    LEFT OUTER JOIN (	SELECT id, state, price_day_total, room_id, date, reservation_id
                                        FROM pms_reservation_line
                                        WHERE pms_property_id = %s AND state != 'cancel'
                                        AND occupies_availability = true AND date <= %s
                    ) l ON l.room_id = dr.room_id AND l.date = dr.date
                    LEFT OUTER JOIN (	SELECT 	date, room_type_id, min_stay, min_stay_arrival, max_stay,
                                            max_stay_arrival, closed, closed_departure, closed_arrival
                                        FROM pms_availability_plan_rule
                                        WHERE availability_plan_id = %s and pms_property_id = %s
                    ) ru ON ru.date = dr.date AND ru.room_type_id = dr.room_type_id
                    LEFT OUTER JOIN pms_reservation r ON l.reservation_id = r.id
                    LEFT OUTER JOIN pms_folio f ON r.folio_id = f.id
                    ORDER BY dr.sequence, dr.room_id, dr.date
                    """,
            (
                calendar_search_param.dateFrom,
                calendar_search_param.dateTo,
                calendar_search_param.pmsPropertyId,
                calendar_search_param.pmsPropertyId,
                calendar_search_param.dateTo,
                calendar_search_param.availabilityPlanId,
                calendar_search_param.pmsPropertyId,
            ),
        )
        result = self.env.cr.dictfetchall()
        CalendarRenderInfo = self.env.datamodels["pms.calendar.render.info"]
        last_room_id = False
        last_reservation_id = False
        index_date_last_reservation = False
        for index, item in enumerate(result):
            date = {
                "date": datetime.combine(item['date'], datetime.min.time()).isoformat(),
                "reservationLines": [],
            }
            restriction = build_restriction(item)
            if restriction:
                date.update({
                    "restriction": restriction,
                })

            if last_room_id != item['room_id']:
                last_room_id = item['room_id']
                last_reservation_id = False
                response.append(
                    CalendarRenderInfo(
                        roomId=item["room_id"],
                        capacity=item["capacity"],
                        roomTypeClassId=item["room_type_class_id"],
                        roomTypeId=item["room_type_id"],
                        dates=[
                            date
                        ],
                    )
                )
            else:
                response[-1].dates.append(
                    date
                )
            if item['reservation_id'] is not None and item['reservation_id'] != last_reservation_id:
                response[-1].dates[-1]['reservationLines'].append(
                    build_reservation_line_info(
                        item,
                        previous_item=False
                        if (not item["splitted"] or item["date"] == date_from)
                        else result[index - 1],
                        next_item=False
                        if (not item["splitted"] or item["date"] == date_to)
                        else result[index + 1],
                    )
                )
                last_reservation_id = item['reservation_id']
                index_date_last_reservation = len(response[-1].dates) - 1
            elif item['reservation_id'] is not None and item['reservation_id'] == last_reservation_id:
                response[-1].dates[index_date_last_reservation]['reservationLines'].append(
                    build_reservation_line_info(
                        item,
                        previous_item=False
                        if (not item["splitted"] or item["date"] == date_from)
                        else result[index - 1],
                        next_item=False
                        if (not item["splitted"] or item["date"] == date_to)
                        else result[index + 1],
                    )
                )
                last_reservation_id = item['reservation_id']
            else:
                last_reservation_id = False
        return response

    @restapi.method(
        [
            (
                [
                    "/calendar-prices-rules",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.calendar.search.param"),
        output_param=Datamodel("pms.calendar.prices.rules.render.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_prices_rules_calendar(self, calendar_search_param):
        response = []
        date_from = datetime.strptime(calendar_search_param.dateFrom, "%Y-%m-%d").date()
        date_to = datetime.strptime(calendar_search_param.dateTo, "%Y-%m-%d").date()

        self.env.cr.execute(
            f"""
                SELECT dr.room_type_id,
                dr.date date,
                it.id pricelist_item_id,
                av.id availability_plan_rule_id,
                COALESCE(av.max_avail, dr.default_max_avail) max_avail,
                COALESCE(av.quota, dr.default_quota) quota,
                COALESCE(av.closed, FALSE) closed,
                COALESCE(av.closed_arrival, FALSE) closed_arrival,
                COALESCE(av.closed_Departure, FALSE) closed_departure,
                COALESCE(av.min_stay, 0) min_stay,
                COALESCE(av.min_stay_arrival, 0) min_stay_arrival,
                COALESCE(av.max_stay, 0) max_stay,
                COALESCE(av.max_stay_arrival, 0) max_stay_arrival,
                COALESCE(it.fixed_price, (
                    SELECT ipp.value_float
                    FROM ir_pms_property ipp, (SELECT id field_id, model_id
                                                FROM ir_model_fields
                                                WHERE name = 'list_price' AND model = 'product.template'
                                                ) imf
                    WHERE ipp.model_id = imf.model_id
                    AND ipp.field_id = imf.field_id
                    AND ipp.record = pp.product_tmpl_id
                    AND ipp.pms_property_id = %s
                    )
                ) price,
                (SELECT COUNT (1)
                    FROM pms_room r
                    WHERE r.room_type_id = dr.room_type_id AND r.active = true AND r.pms_property_id = %s
                    AND NOT EXISTS (SELECT 1
                                    FROM pms_reservation_line
                                    WHERE date = dr.date
                                    AND occupies_availability = true
                                    AND room_id = r.id
                                    AND r.is_shared_room = false)
                 ) free_rooms
                FROM
                (
                    SELECT dates.date, rt_r.room_type_id, rt_r.product_id, rt_r.default_max_avail, rt_r.default_quota
                    FROM
                    (
                        SELECT (CURRENT_DATE + date) date
                        FROM generate_series(date %s- CURRENT_DATE, date %s - CURRENT_DATE) date
                    ) dates,
                    (
                        SELECT  rt.id room_type_id,
                                rt.product_id,
                                rt.default_max_avail,
                                rt.default_quota
                        FROM pms_room_type rt
                        WHERE EXISTS (  SELECT 1
                                        FROM pms_room
                                        WHERE pms_property_id = %s
                                        AND room_type_id = rt.id
                                        AND active = true)
                    ) rt_r
                ) dr
                INNER JOIN product_product pp ON pp.id = dr.product_id
                LEFT OUTER JOIN pms_availability_plan_rule av ON av.date = dr.date
                    AND av.room_type_id = dr.room_type_id
                    AND av.pms_property_id = %s
                    AND av.availability_plan_id = %s
                LEFT OUTER JOIN product_pricelist_item it ON it.date_start_consumption = dr.date
                    AND it.date_end_consumption = dr.date
                    AND it.product_id = dr.product_id
                    AND it.active = true
                    AND it.pricelist_id = %s
                AND EXISTS (SELECT 1
                            FROM product_pricelist_item_pms_property_rel relp
                            WHERE relp.product_pricelist_item_id = it.id AND relp.pms_property_id = %s)
                ORDER BY dr.room_type_id, dr.date;
            """,
            (
                calendar_search_param.pmsPropertyId,
                calendar_search_param.pmsPropertyId,
                date_from,
                date_to,
                calendar_search_param.pmsPropertyId,
                calendar_search_param.pmsPropertyId,
                calendar_search_param.availabilityPlanId,
                calendar_search_param.pricelistId,
                calendar_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        CalendarPricesRulesRenderInfo = self.env.datamodels["pms.calendar.prices.rules.render.info"]
        last_room_type_id = False
        for index, item in enumerate(result):
            date = {
                "date": datetime.combine(item['date'], datetime.min.time()).isoformat(),
                "freeRooms": item['free_rooms'],
                "pricelistItemId": item['pricelist_item_id'],
                "price": item['price'],
                #
                "availabilityPlanRuleId": item['availability_plan_rule_id'],
                "maxAvail": item['max_avail'],
                "quota": item['quota'],

                "closed": item['closed'],
                "closedArrival": item['closed_arrival'],
                "closedDeparture": item['closed_departure'],

                "minStay": item['min_stay'],
                "minStayArrival": item['min_stay_arrival'],
                "maxStay": item['max_stay'],
                "maxStayArrival": item['max_stay_arrival'],
            }
            if last_room_type_id != item['room_type_id']:
                last_room_type_id = item['room_type_id']
                response.append(
                    CalendarPricesRulesRenderInfo(
                        roomTypeId=item["room_type_id"],
                        dates=[date],
                    )
                )
            else:
                response[-1].dates.append(date)
        return response

    @restapi.method(
        [
            (
                [
                    "/calendar-headers",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.calendar.header.search.param"),
        output_param=Datamodel("pms.calendar.header.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_calendar_headers(self, calendar_search_param):
        response = []
        date_from = datetime.strptime(calendar_search_param.dateFrom, "%Y-%m-%d").date()
        date_to = datetime.strptime(calendar_search_param.dateTo, "%Y-%m-%d").date()

        room_ids = tuple(calendar_search_param.roomIds)

        self.env.cr.execute(
            f"""
            SELECT d.date,
            bool_or(l.overbooking) overbooking,
            CEIL(SUM(l.price_day_total)) daily_billing,
            tr.num_total_rooms
            -
            (
                SELECT COUNT(1)
                FROM pms_reservation_line
                WHERE date = d.date
                AND pms_property_id = %s
                AND state != 'cancel'
                AND occupies_availability = true
                AND room_id IN %s
            ) free_rooms,
            CEIL((
                SELECT COUNT(1)
                FROM pms_reservation_line l
                INNER JOIN pms_reservation r  ON r.id = l.reservation_id
                WHERE r.reservation_type NOT IN ('out', 'staff')
                AND r.pms_property_id = %s
                AND l.occupies_availability = true
                AND l.state != 'cancel'
                AND l.room_id IN %s
                AND l.date = d.date
            ) * 100.00 / tr.num_total_rooms) occupancy_rate
            FROM (
                    SELECT (CURRENT_DATE + date) date
                    FROM generate_series(date %s- CURRENT_DATE, date %s - CURRENT_DATE
            ) date) d
            LEFT OUTER JOIN (	SELECT date, price_day_total, overbooking
                                FROM pms_reservation_line
                                WHERE pms_property_id = %s
                                AND room_id IN %s
            ) l ON l.date = d.date,
            (	SELECT COUNT(1) num_total_rooms
                FROM pms_room
                WHERE pms_property_id = %s
                AND id IN %s
            ) tr
            GROUP BY d.date, tr.num_total_rooms
            ORDER BY d.date;
            """,
            (
                calendar_search_param.pmsPropertyId,
                room_ids,
                calendar_search_param.pmsPropertyId,
                room_ids,
                date_from,
                date_to,
                calendar_search_param.pmsPropertyId,
                room_ids,
                calendar_search_param.pmsPropertyId,
                room_ids,
            ),
        )

        result = self.env.cr.dictfetchall()
        CalendarHeaderInfo = self.env.datamodels["pms.calendar.header.info"]

        for item in result:
            response.append(
                CalendarHeaderInfo(
                    date=datetime.combine(item['date'], datetime.min.time()).isoformat(),
                    dailyBilling=item["daily_billing"] if item["daily_billing"] else 0,
                    freeRooms=item["free_rooms"] if item["free_rooms"] else 0,
                    occupancyRate=item["occupancy_rate"] if item["occupancy_rate"] else 0,
                    overbooking=item["overbooking"] if item["overbooking"] else False,
                )
            )

        return response

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
