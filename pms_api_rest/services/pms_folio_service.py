from datetime import datetime, timedelta

from odoo import _, fields
from odoo.exceptions import MissingError
from odoo.osv import expression

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsFolioService(Component):
    _inherit = "base.rest.service"
    _name = "pms.folio.service"
    _usage = "folios"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.folio.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_folio(self, folio_id):
        folio = self.env["pms.folio"].search(
            [
                ("id", "=", folio_id),
            ]
        )
        if folio:
            PmsFolioInfo = self.env.datamodels["pms.folio.info"]
            return PmsFolioInfo(
                id=folio.id,
                name=folio.name,
                partnerName=folio.partner_name if folio.partner_name else None,
                partnerPhone=folio.mobile if folio.mobile else None,
                partnerEmail=folio.email if folio.email else None,
                state=dict(folio.fields_get(["state"])["state"]["selection"])[
                    folio.state
                ],
                amountTotal=folio.amount_total,
            )
        else:
            raise MissingError(_("Folio not found"))

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.folio.search.param"),
        output_param=Datamodel("pms.folio.short.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folios(self, folio_search_param):
        domain_fields = list()

        domain_fields.append(("pms_property_id", "=", folio_search_param.pmsPropertyId))

        if folio_search_param.dateTo and folio_search_param.dateFrom:
            date_from = fields.Date.from_string(folio_search_param.dateFrom)
            date_to = fields.Date.from_string(folio_search_param.dateTo)
            dates = [
                date_from + timedelta(days=x)
                for x in range(0, (date_to - date_from).days + 1)
            ]
            reservation_lines = list(
                set(
                    self.env["pms.reservation.line"]
                    .search([("date", "in", dates)])
                    .mapped("reservation_id")
                    .mapped("folio_id")
                    .ids
                )
            )
            domain_fields.append(("folio_id", "in", reservation_lines))

        domain_filter = list()
        if folio_search_param.filter:
            for search in folio_search_param.filter.split(" "):
                subdomains = [
                    [("name", "ilike", search)],
                    [("folio_id.name", "ilike", search)],
                    [("partner_name", "ilike", search)],
                    [("partner_id.firstname", "ilike", search)],
                    [("partner_id.lastname", "ilike", search)],
                    [("partner_id.id_numbers.name", "ilike", search)],
                ]
                domain_filter.append(expression.OR(subdomains))
        domain = []
        if domain_filter:
            domain = expression.AND([domain_fields, domain_filter[0]])
        else:
            domain = domain_fields
        result_folios = []

        reservations_result = (
            self.env["pms.reservation"].search(domain).mapped("folio_id").ids
        )

        PmsFolioShortInfo = self.env.datamodels["pms.folio.short.info"]
        for folio in self.env["pms.folio"].search(
            [("id", "in", reservations_result)],
        ):
            reservations = []
            for reservation in folio.reservation_ids:
                reservations.append(
                    {
                        "id": reservation.id,
                        "checkin": datetime.combine(
                            reservation.checkin, datetime.min.time()
                        ).isoformat(),
                        "checkout": datetime.combine(
                            reservation.checkout, datetime.min.time()
                        ).isoformat(),
                        "preferredRoomShortName": reservation.preferred_room_id.short_name
                        if reservation.preferred_room_id
                        else None,
                        "adults": reservation.adults,
                        "pricelistName": reservation.pricelist_id.name,
                        "saleChannel": reservation.channel_type_id.name
                        if reservation.channel_type_id
                        else None,
                        "agency": reservation.agency_id.name
                        if reservation.agency_id
                        else None,
                        "agencyImage": reservation.agency_id.image_1024.decode("utf-8")
                        if reservation.agency_id and reservation.agency_id.image_1024
                        else None,
                    }
                )
            result_folios.append(
                PmsFolioShortInfo(
                    id=folio.id,
                    partnerName=folio.partner_name if folio.partner_name else None,
                    partnerPhone=folio.mobile if folio.mobile else None,
                    partnerEmail=folio.email if folio.email else None,
                    amountTotal=folio.amount_total,
                    reservations=[] if not reservations else reservations,
                    paymentState=dict(
                        folio.fields_get(["payment_state"])["payment_state"][
                            "selection"
                        ]
                    )[folio.payment_state]
                    if folio.payment_state
                    else None,
                )
            )
        return result_folios

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/payments",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.search.param"),
        output_param=Datamodel("pms.payment.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_payments(self, folio_id, pms_search_param):
        domain = list()
        domain.append(("id", "=", folio_id))
        domain.append(("pms_property_id", "=", pms_search_param.pmsPropertyId))
        folio = self.env["pms.folio"].search(domain)
        payments = []
        PmsPaymentInfo = self.env.datamodels["pms.payment.info"]
        if not folio:
            pass
        else:
            if folio.payment_state == "not_paid":
                pass
                # si el folio está sin pagar no tendrá ningún pago o envíar []?
            else:
                if folio.statement_line_ids:
                    for payment in folio.statement_line_ids:
                        payments.append(
                            PmsPaymentInfo(
                                id=payment.id,
                                amount=payment.amount,
                                journalId=payment.journal_id,
                                journalName=payment.journal_id.name,
                                date=str(payment.date),
                            )
                        )
                if folio.payment_ids:
                    if folio.payment_ids:
                        for payment in folio.payment_ids:
                            payments.append(
                                PmsPaymentInfo(
                                    id=payment.id,
                                    amount=payment.amount,
                                    journalId=payment.journal_id,
                                    journalName=payment.journal_id.name,
                                    date=str(payment.date),
                                )
                            )
        return payments

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/reservations",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.reservation.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_reservations(self, folio_id):
        folio = self.env["pms.folio"].browse(folio_id)
        reservations = []
        PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]
        if not folio:
            pass
        else:
            if folio.reservation_ids:
                for reservation in folio.reservation_ids:
                    reservations.append(
                        PmsReservationShortInfo(
                            id=reservation.id,
                            boardServiceName=reservation.board_service_room_id.pms_board_service_id.name
                            or None,
                            checkin=datetime.combine(
                                reservation.checkin, datetime.min.time()
                            ).isoformat(),
                            checkout=datetime.combine(
                                reservation.checkout, datetime.min.time()
                            ).isoformat(),
                            roomTypeName=reservation.room_type_id.name or None,
                            preferredRoomShortName=reservation.preferred_room_id.short_name
                            or None,
                            adults=reservation.adults,
                            state=dict(
                                reservation.fields_get(["state"])["state"]["selection"]
                            )[reservation.state],
                            children=reservation.children or None,
                            readyForCheckin=reservation.ready_for_checkin,
                            allowedCheckout=reservation.allowed_checkout,
                            isSplitted=reservation.splitted,
                            priceTotal=reservation.price_room_services_set,
                            servicesCount=len(
                                reservation.service_ids.filtered(
                                    lambda x: not x.is_board_service
                                )
                            ),
                        )
                    )

        return reservations

    # @restapi.method(
    #     [
    #         (
    #             [
    #                 "/",
    #             ],
    #             "POST",
    #         )
    #     ],
    #     input_param=Datamodel("pms.reservation.info", is_list=False),
    #     auth="jwt_api_pms",
    # )
    # def create_reservation(self, pms_reservation_info):
    #     reservation = self.env["pms.reservation"].create(
    #         {
    #             "partner_name": pms_reservation_info.partner,
    #             "pms_property_id": pms_reservation_info.pmsPropertyId,
    #             "room_type_id": pms_reservation_info.roomTypeId,
    #             "pricelist_id": pms_reservation_info.pricelistId,
    #             "checkin": pms_reservation_info.checkin,
    #             "checkout": pms_reservation_info.checkout,
    #             "board_service_room_id": pms_reservation_info.boardServiceId,
    #             "channel_type_id": pms_reservation_info.channelTypeId,
    #         }
    #     )
    #     return reservation.id
