from datetime import datetime

from odoo import fields

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsDashboardServices(Component):
    _inherit = "base.rest.service"
    _name = "pms.dashboard.service"
    _usage = "dashboard"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/pending-reservations",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.range.dates.search.param"),
        output_param=Datamodel("pms.dashboard.pending.reservations", is_list=True),
        auth="jwt_api_pms",
    )
    def get_pending_reservations(self, pms_dashboard_search_param):
        dateFrom = fields.Date.from_string(pms_dashboard_search_param.dateFrom)
        dateTo = fields.Date.from_string(pms_dashboard_search_param.dateTo)

        self.env.cr.execute(
            """
            SELECT
            d.date,
            SUM(CASE WHEN r.checkin = d.date AND r.state IN ('confirm', 'arrival_delayed')
            THEN 1 ELSE 0
            END) AS reservations_pending_arrival,
            SUM(CASE WHEN r.checkin = d.date AND r.state = 'onboard' THEN 1 ELSE 0
            END) AS
            reservations_on_board,
            SUM(CASE WHEN r.checkout = d.date AND r.state IN ('onboard', 'departure_delayed')
            THEN 1 ELSE 0
            END) AS reservations_pending_departure,
            SUM(CASE WHEN r.checkout = d.date AND r.state = 'done' THEN 1 ELSE 0 END)
            AS reservations_completed
            FROM ( SELECT CURRENT_DATE + date AS date
            FROM generate_series(date %s - CURRENT_DATE, date %s - CURRENT_DATE) date) d
            LEFT JOIN pms_reservation r
            ON (r.checkin = d.date OR r.checkout = d.date)
            AND r.pms_property_id = %s
            AND r.reservation_type != 'out'
            GROUP BY d.date
            ORDER BY d.date;
            """,
            (
                dateFrom,
                dateTo,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        pending_reservations = []
        DashboardPendingReservations = self.env.datamodels[
            "pms.dashboard.pending.reservations"
        ]

        for item in result:
            pending_reservations.append(
                DashboardPendingReservations(
                    date=datetime.combine(
                        item["date"], datetime.min.time()
                    ).isoformat(),
                    pendingArrivalReservations=item["reservations_pending_arrival"]
                    if item["reservations_pending_arrival"]
                    else 0,
                    completedArrivalReservations=item["reservations_on_board"]
                    if item["reservations_on_board"]
                    else 0,
                    pendingDepartureReservations=item["reservations_pending_departure"]
                    if item["reservations_pending_departure"]
                    else 0,
                    completedDepartureReservations=item["reservations_completed"]
                    if item["reservations_completed"]
                    else 0,
                )
            )
        return pending_reservations

    @restapi.method(
        [
            (
                [
                    "/occupancy",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_occupancy(self, pms_dashboard_search_param):
        date_occupancy = fields.Date.from_string(pms_dashboard_search_param.date)

        self.env.cr.execute(
            """
            SELECT CEIL(l.num * 100.00 / tr.num_total_rooms)  AS occupancy
            FROM
            (
                SELECT COUNT(1) num_total_rooms
                FROM pms_room
                WHERE pms_property_id = %s
            ) tr,
            (
                SELECT COUNT(1) num
                FROM pms_reservation_line l
                INNER JOIN pms_reservation r  ON r.id = l.reservation_id
                WHERE r.reservation_type NOT IN ('out', 'staff')
                AND l.occupies_availability = true
                AND l.state != 'cancel'
                AND l.date = %s
                AND r.pms_property_id = %s
            ) l
            """,
            (
                pms_dashboard_search_param.pmsPropertyId,
                date_occupancy,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]

        return DashboardNumericResponse(
            value=result[0]["occupancy"] if result[0]["occupancy"] else 0,
        )

    @restapi.method(
        [
            (
                [
                    "/state-rooms",
                ],
                "GET",
            )
        ],
        auth="jwt_api_pms",
        input_param=Datamodel("pms.dashboard.range.dates.search.param"),
        output_param=Datamodel("pms.dashboard.state.rooms", is_list=True),
    )
    def get_state_rooms(self, pms_dashboard_search_param):
        dateFrom = fields.Date.from_string(pms_dashboard_search_param.dateFrom)
        dateTo = fields.Date.from_string(pms_dashboard_search_param.dateTo)
        self.env.cr.execute(
            """
                SELECT 	d.date,
                COALESCE(rln.num_occupied_rooms, 0) AS num_occupied_rooms,
                COALESCE( rlo.num_out_of_service_rooms, 0) AS num_out_of_service_rooms,
                COUNT(r.id) free_rooms
                FROM
                (
                    SELECT (CURRENT_DATE + date) date
                    FROM generate_series(date %s- CURRENT_DATE, date %s - CURRENT_DATE
                ) date) d
                LEFT OUTER JOIN (SELECT COUNT(1) num_occupied_rooms, date
                                 FROM pms_reservation_line l
                                 INNER JOIN pms_reservation r ON l.reservation_id = r.id
                                 WHERE l.pms_property_id = %s
                                 AND l.occupies_availability
                                 AND r.reservation_type != 'out'
                                 GROUP BY date
                ) rln ON rln.date = d.date
                LEFT OUTER JOIN (SELECT COUNT(1) num_out_of_service_rooms, date
                                 FROM pms_reservation_line l
                                 INNER JOIN pms_reservation r ON l.reservation_id = r.id
                                 WHERE l.pms_property_id = %s
                                 AND l.occupies_availability
                                 AND r.reservation_type = 'out'
                                 GROUP BY date
                ) rlo ON rlo.date = d.date,
                pms_room r
                WHERE r.pms_property_id = %s
                AND r.id NOT IN (SELECT room_id
                                 FROM pms_reservation_line l
                                 WHERE l.date = d.date
                                 AND l.occupies_availability
                                 AND l.pms_property_id = %s
                                )
                GROUP BY d.date, num_occupied_rooms, num_out_of_service_rooms
                ORDER BY d.date
                    """,
            (
                dateFrom,
                dateTo,
                pms_dashboard_search_param.pmsPropertyId,
                pms_dashboard_search_param.pmsPropertyId,
                pms_dashboard_search_param.pmsPropertyId,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        state_rooms_result = []
        DashboardStateRooms = self.env.datamodels["pms.dashboard.state.rooms"]
        for item in result:
            state_rooms_result.append(
                DashboardStateRooms(
                    date=datetime.combine(
                        item["date"], datetime.min.time()
                    ).isoformat(),
                    numOccupiedRooms=item["num_occupied_rooms"]
                    if item["num_occupied_rooms"]
                    else 0,
                    numOutOfServiceRooms=item["num_out_of_service_rooms"]
                    if item["num_out_of_service_rooms"]
                    else 0,
                    numFreeRooms=item["free_rooms"] if item["free_rooms"] else 0,
                )
            )
        return state_rooms_result

    @restapi.method(
        [
            (
                [
                    "/reservations-by-sale-channel",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.range.dates.search.param"),
        output_param=Datamodel("pms.dashboard.state.rooms", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservations_by_sale_channel(self, pms_dashboard_search_param):
        dateFrom = fields.Date.from_string(pms_dashboard_search_param.dateFrom)
        dateTo = fields.Date.from_string(pms_dashboard_search_param.dateTo)
        self.env.cr.execute(
            """
                SELECT CASE WHEN sc.channel_type = 'direct' THEN sc.name
                        ELSE (SELECT name FROM res_partner WHERE id = r.agency_id)
                END AS sale_channel_name,
                CEIL(COUNT(r.id) * 100.00 / tr.num_total_reservations)
                AS percentage_by_sale_channel
                FROM
                (
                    SELECT COUNT(1) num_total_reservations
                    FROM pms_reservation
                    WHERE create_date::date BETWEEN %s AND %s
                    AND reservation_type != 'out'
                    AND pms_property_id = %s
                ) tr,
                pms_reservation r
                INNER JOIN pms_sale_channel sc ON r.sale_channel_origin_id = sc.id
                WHERE r.create_date::date BETWEEN %s AND %s
                AND r.reservation_type != 'out'
                AND r.pms_property_id = %s
                GROUP BY
                    r.sale_channel_origin_id,
                    sc.channel_type, sc.name,
                    r.agency_id,
                    tr.num_total_reservations
                ORDER BY percentage_by_sale_channel DESC;
                """,
            (
                dateFrom,
                dateTo,
                pms_dashboard_search_param.pmsPropertyId,
                dateFrom,
                dateTo,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        state_rooms_result = []
        DashboardReservationsBySaleChannel = self.env.datamodels[
            "pms.dashboard.reservations.by.sale.channel"
        ]
        for item in result:
            state_rooms_result.append(
                DashboardReservationsBySaleChannel(
                    saleChannelName=item["sale_channel_name"]
                    if item["sale_channel_name"]
                    else "",
                    percentageReservationsSoldBySaleChannel=item[
                        "percentage_by_sale_channel"
                    ]
                    if item["percentage_by_sale_channel"]
                    else 0,
                )
            )
        return state_rooms_result

    @restapi.method(
        [
            (
                [
                    "/billing",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_billing(self, pms_dashboard_search_param):
        date_billing = fields.Date.from_string(pms_dashboard_search_param.date)

        self.env.cr.execute(
            """
            SELECT SUM(l.price_day_total) billing
            FROM pms_reservation_line l INNER JOIN pms_reservation r ON l.reservation_id = r.id
            WHERE l.date = %s
            AND l.occupies_availability = true
            AND l.state != 'cancel'
            AND l.pms_property_id = %s
            AND r.reservation_type NOT IN ('out', 'staff')
            """,
            (
                date_billing,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]
        return DashboardNumericResponse(
            value=result[0]["billing"] if result[0]["billing"] else 0,
        )

    @restapi.method(
        [
            (
                [
                    "/adr",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.range.dates.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_adr(self, pms_dashboard_search_param):
        date_from = fields.Date.from_string(pms_dashboard_search_param.dateFrom)
        date_to = fields.Date.from_string(pms_dashboard_search_param.dateTo)

        pms_property = self.env["pms.property"].search(
            [("id", "=", pms_dashboard_search_param.pmsPropertyId)]
        )

        adr = pms_property._get_adr(date_from, date_to)

        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]

        return DashboardNumericResponse(
            value=adr,
        )

    @restapi.method(
        [
            (
                [
                    "/revpar",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.range.dates.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_revpar(self, pms_dashboard_search_param):
        date_from = fields.Date.from_string(pms_dashboard_search_param.dateFrom)
        date_to = fields.Date.from_string(pms_dashboard_search_param.dateTo)

        pms_property = self.env["pms.property"].search(
            [("id", "=", pms_dashboard_search_param.pmsPropertyId)]
        )

        revpar = pms_property._get_revpar(date_from, date_to)

        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]

        return DashboardNumericResponse(
            value=revpar,
        )

    @restapi.method(
        [
            (
                [
                    "/new-folios",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_number_of_new_folios(self, pms_dashboard_search_param):
        date_new_folios = fields.Date.from_string(pms_dashboard_search_param.date)

        self.env.cr.execute(
            """
             SELECT COUNT(1) new_folios
                FROM pms_folio f
                WHERE DATE(f.create_date) = %s
                AND f.state != 'cancel'
                AND f.pms_property_id = %s
                AND f.reservation_type NOT IN ('out', 'staff')
            """,
            (
                date_new_folios,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]

        return DashboardNumericResponse(
            value=result[0]["new_folios"] if result[0]["new_folios"] else 0,
        )

    @restapi.method(
        [
            (
                [
                    "/overnights",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_overnights(self, pms_dashboard_search_param):
        date = fields.Date.from_string(pms_dashboard_search_param.date)

        self.env.cr.execute(
            """
              SELECT COUNT(1) overnights
                FROM pms_reservation_line l
                INNER JOIN pms_reservation r ON r.id = l.reservation_id
                WHERE l.date = %s
                AND l.state != 'cancel'
                AND l.occupies_availability = true
                AND l.pms_property_id = %s
                AND l.overbooking = false
                AND r.reservation_type != 'out'
            """,
            (
                date,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]

        return DashboardNumericResponse(
            value=result[0]["overnights"] if result[0]["overnights"] else 0,
        )

    @restapi.method(
        [
            (
                [
                    "/cancelled-overnights",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_cancelled_overnights(self, pms_dashboard_search_param):
        date = fields.Date.from_string(pms_dashboard_search_param.date)

        self.env.cr.execute(
            """
              SELECT COUNT(1) cancelled_overnights
                FROM pms_reservation_line l
                INNER JOIN pms_reservation r ON r.id = l.reservation_id
                WHERE l.date = %s
                AND l.state = 'cancel'
                AND l.occupies_availability = false
                AND l.pms_property_id = %s
                AND l.overbooking = false
                AND r.reservation_type != 'out'
            """,
            (
                date,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]

        return DashboardNumericResponse(
            value=result[0]["cancelled_overnights"]
            if result[0]["cancelled_overnights"]
            else 0,
        )

    @restapi.method(
        [
            (
                [
                    "/overbookings",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.search.param"),
        output_param=Datamodel("pms.dashboard.numeric.response"),
        auth="jwt_api_pms",
    )
    def get_overbookings(self, pms_dashboard_search_param):
        date = fields.Date.from_string(pms_dashboard_search_param.date)

        self.env.cr.execute(
            """
              SELECT COUNT(1) overbookings
                FROM pms_reservation_line l
                WHERE l.date = %s
                AND l.pms_property_id = %s
                AND l.overbooking = true
            """,
            (
                date,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        DashboardNumericResponse = self.env.datamodels["pms.dashboard.numeric.response"]

        return DashboardNumericResponse(
            value=result[0]["overbookings"] if result[0]["overbookings"] else 0,
        )

    @restapi.method(
        [
            (
                [
                    "/occupied-rooms",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.range.dates.search.param"),
        output_param=Datamodel("pms.dashboard.state.rooms", is_list=True),
        auth="jwt_api_pms",
    )
    def get_occupied_rooms(self, pms_dashboard_search_param):
        dateFrom = fields.Date.from_string(pms_dashboard_search_param.dateFrom)
        dateTo = fields.Date.from_string(pms_dashboard_search_param.dateTo)
        self.env.cr.execute(
            """
            SELECT 	d.date, COALESCE(rln.num_occupied_rooms, 0) AS num_occupied_rooms
            FROM
            (
                SELECT (CURRENT_DATE + date) date
                FROM generate_series(date %s- CURRENT_DATE, date %s - CURRENT_DATE
            ) date) d
            LEFT OUTER JOIN (SELECT COUNT(1) num_occupied_rooms, date
                             FROM pms_reservation_line l
                             INNER JOIN pms_reservation r ON l.reservation_id = r.id
                             WHERE l.pms_property_id = %s
                             AND l.occupies_availability
                             AND r.reservation_type != 'out'
                             GROUP BY date
            ) rln ON rln.date = d.date
            GROUP BY d.date, num_occupied_rooms
            ORDER BY d.date
            """,
            (
                dateFrom,
                dateTo,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        occupied_rooms_result = []
        DashboardStateRooms = self.env.datamodels["pms.dashboard.state.rooms"]
        for item in result:
            occupied_rooms_result.append(
                DashboardStateRooms(
                    date=datetime.combine(
                        item["date"], datetime.min.time()
                    ).isoformat(),
                    numOccupiedRooms=item["num_occupied_rooms"]
                    if item["num_occupied_rooms"]
                    else 0,
                )
            )
        return occupied_rooms_result

    @restapi.method(
        [
            (
                [
                    "/daily-billings",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.dashboard.range.dates.search.param"),
        output_param=Datamodel("pms.dashboard.state.rooms", is_list=True),
        auth="jwt_api_pms",
    )
    def get_daily_billings(self, pms_dashboard_search_param):
        dateFrom = fields.Date.from_string(pms_dashboard_search_param.dateFrom)
        dateTo = fields.Date.from_string(pms_dashboard_search_param.dateTo)
        self.env.cr.execute(
            """
            SELECT 	d.date, COALESCE(rln.daily_billing, 0) AS daily_billing
            FROM
            (
                SELECT (CURRENT_DATE + date) date
                FROM generate_series(date %s - CURRENT_DATE, date %s - CURRENT_DATE
            ) date) d
            LEFT OUTER JOIN (SELECT sum(l.price_day_total) daily_billing, date
                             FROM pms_reservation_line l
                             INNER JOIN pms_reservation r ON l.reservation_id = r.id
                             WHERE l.pms_property_id = %s
                             AND l.occupies_availability
                             AND r.reservation_type != 'out'
                             GROUP BY date
            ) rln ON rln.date = d.date
            GROUP BY d.date, daily_billing
            ORDER BY d.date;
            """,
            (
                dateFrom,
                dateTo,
                pms_dashboard_search_param.pmsPropertyId,
            ),
        )

        result = self.env.cr.dictfetchall()
        result_daily_billings = []
        DashboardStateRooms = self.env.datamodels["pms.dashboard.daily.billing"]
        for item in result:
            result_daily_billings.append(
                DashboardStateRooms(
                    date=datetime.combine(
                        item["date"], datetime.min.time()
                    ).isoformat(),
                    billing=item["daily_billing"] if item["daily_billing"] else 0,
                )
            )
        return result_daily_billings

    @restapi.method(
        [
            (
                [
                    "/last-received-folios",
                ],
                "GET",
            ),
        ],
        input_param=Datamodel("pms.folio.search.param", is_list=False),
        output_param=Datamodel("pms.folio.short.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_last_received_folios(self, pms_folio_search_param):
        result_folios = []
        PmsFolioShortInfo = self.env.datamodels["pms.folio.short.info"]
        for folio in self.env["pms.folio"].search(
            [
                ("first_checkin", ">=", datetime.now().date()),
                ("pms_property_id", "=", pms_folio_search_param.pmsPropertyId),
            ],
            limit=pms_folio_search_param.limit,
            offset=pms_folio_search_param.offset,
            order="create_date desc",
        ):
            result_folios.append(
                PmsFolioShortInfo(
                    id=folio.id,
                    name=folio.name,
                    state=folio.state,
                    partnerName=folio.partner_name if folio.partner_name else None,
                    partnerPhone=folio.mobile if folio.mobile else None,
                    partnerEmail=folio.email if folio.email else None,
                    amountTotal=round(folio.amount_total, 2),
                    pendingAmount=round(folio.pending_amount, 2),
                    paymentStateCode=folio.payment_state,
                    paymentStateDescription=dict(
                        folio.fields_get(["payment_state"])["payment_state"][
                            "selection"
                        ]
                    )[folio.payment_state],
                    numReservations=len(folio.reservation_ids),
                    reservationType=folio.reservation_type,
                    closureReasonId=folio.closure_reason_id,
                    agencyId=folio.agency_id.id if folio.agency_id else None,
                    pricelistId=folio.pricelist_id.id if folio.pricelist_id else None,
                    saleChannelId=folio.sale_channel_origin_id.id
                    if folio.sale_channel_origin_id
                    else None,
                    firstCheckin=str(folio.first_checkin),
                    lastCheckout=str(folio.last_checkout),
                    createHour=folio.create_date.strftime("%H:%M"),
                )
            )
        return result_folios

    @restapi.method(
        [
            (
                [
                    "/num-last-received-folios",
                ],
                "GET",
            ),
        ],
        input_param=Datamodel("pms.folio.search.param", is_list=False),
        auth="jwt_api_pms",
    )
    def get_num_last_received_folios(self, pms_folio_search_param):
        return self.env["pms.folio"].search_count(
            [
                ("first_checkin", ">=", datetime.now().date()),
                ("pms_property_id", "=", pms_folio_search_param.pmsPropertyId),
            ],
        )
