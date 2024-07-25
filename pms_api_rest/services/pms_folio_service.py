import base64
import logging
from datetime import datetime, timedelta

import pytz

from odoo import _, fields
from odoo.exceptions import MissingError, ValidationError
from odoo.osv import expression
from odoo.tools import get_lang

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import url_image_pms_api_rest

_logger = logging.getLogger(__name__)


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
            portal_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                + folio.get_portal_url()
            )
            PmsFolioInfo = self.env.datamodels["pms.folio.info"]
            return PmsFolioInfo(
                id=folio.id,
                name=folio.name,
                partnerId=folio.partner_id if folio.partner_id else None,
                partnerName=folio.partner_name if folio.partner_name else None,
                partnerPhone=folio.mobile if folio.mobile else None,
                partnerEmail=folio.email if folio.email else None,
                state=folio.state,
                amountTotal=round(folio.amount_total, 2),
                reservationType=folio.reservation_type,
                pendingAmount=folio.pending_amount,
                firstCheckin=str(folio.first_checkin),
                lastCheckout=str(folio.last_checkout),
                createDate=folio.create_date.isoformat(),
                createdBy=folio.create_uid.name,
                internalComment=folio.internal_comment
                if folio.internal_comment
                else None,
                invoiceStatus=folio.invoice_status,
                pricelistId=folio.pricelist_id if folio.pricelist_id else None,
                saleChannelId=folio.sale_channel_origin_id
                if folio.sale_channel_origin_id
                else None,
                agencyId=folio.agency_id if folio.agency_id else None,
                externalReference=folio.external_reference
                if folio.external_reference
                else None,
                closureReasonId=folio.closure_reason_id,
                outOfServiceDescription=folio.out_service_description
                if folio.out_service_description
                else None,
                portalUrl=portal_url,
                language=folio.lang if folio.lang else None,
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
        input_param=Datamodel("pms.folio.search.param", is_list=False),
        output_param=Datamodel("pms.folio.short.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folios(self, folio_search_param):
        domain_fields = list()
        pms_property_id = int(folio_search_param.pmsPropertyId)
        domain_fields.append(("pms_property_id", "=", pms_property_id))
        order_field = "write_date desc"
        if folio_search_param.last:
            order_field = "create_date desc"
        if folio_search_param.dateTo and folio_search_param.dateFrom:
            date_from = fields.Date.from_string(folio_search_param.dateFrom)
            date_to = fields.Date.from_string(folio_search_param.dateTo)
            dates = [
                date_from + timedelta(days=x)
                for x in range(0, (date_to - date_from).days + 1)
            ]
            self.env.cr.execute(
                """
                SELECT folio.id
                FROM    pms_reservation_line  night
                        LEFT JOIN pms_reservation reservation
                            ON reservation.id = night.reservation_id
                        LEFT JOIN pms_folio folio
                            ON folio.id = reservation.folio_id
                WHERE   (night.pms_property_id = %s)
                    AND (night.date in %s)
                GROUP BY folio.id
                """,
                (
                    pms_property_id,
                    tuple(dates),
                ),
            )
            folio_ids = [x[0] for x in self.env.cr.fetchall()]
            domain_fields.append(("folio_id", "in", folio_ids))

        if folio_search_param.createDateFrom and folio_search_param.createDateTo:
            domain_fields.append(
                (
                    "create_date",
                    ">=",
                    datetime.strptime(
                        folio_search_param.createDateFrom, "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )
            domain_fields.append(
                (
                    "create_date",
                    "<=",
                    datetime.strptime(
                        folio_search_param.createDateTo, "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )

        domain_filter = list()
        if folio_search_param.last:
            domain_filter.append([("checkin", ">=", fields.Date.today())])

        if folio_search_param.ids:
            domain_filter.append([("folio_id", "in", folio_search_param.ids)])

        if folio_search_param.filter:
            target = folio_search_param.filter
            if "@" in target:
                domain_filter.append([("email", "ilike", target)])
            else:
                subdomains = [
                    [("name", "ilike", target)],
                    [("partner_name", "ilike", "%".join(target.split(" ")))],
                    [("mobile", "ilike", target)],
                    [("external_reference", "ilike", target)],
                ]
                domain_filter.append(expression.OR(subdomains))
        if folio_search_param.filterByState:
            if folio_search_param.filterByState == "checkinYesterday":
                subdomains = [
                    [("state", "in", ("confirm", "arrival_delayed"))],
                    [("checkin", "=", fields.Date.today() - timedelta(days=1))],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "pendingCheckinToday":
                subdomains = [
                    [("state", "in", ("confirm", "arrival_delayed"))],
                    [("checkin", "=", fields.Date.today())],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "completedCheckinsToday":
                subdomains = [
                    [("state", "=", "onboard")],
                    [("checkin", "=", fields.Date.today())],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "pendingCheckinsTomorrow":
                subdomains = [
                    [("state", "=", "confirm")],
                    [("checkin", "=", fields.Date.today() + timedelta(days=1))],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "pendingCheckoutsToday":
                subdomains = [
                    [("state", "in", ("onboard", "departure_delayed"))],
                    [("checkout", "=", fields.Date.today())],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "pendingCheckoutsTomorrow":
                subdomains = [
                    [("state", "in", ("onboard", "departure_delayed"))],
                    [("checkout", "=", fields.Date.today() + timedelta(days=1))],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "completedCheckoutsToday":
                subdomains = [
                    [("state", "=", "done")],
                    [("checkout", "=", fields.Date.today())],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "completedCheckoutsTomorrow":
                subdomains = [
                    [("state", "=", "done")],
                    [("checkout", "=", fields.Date.today() + timedelta(days=1))],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "byCheckin":
                subdomains = [
                    [("state", "in", ("confirm", "arrival_delayed"))],
                    [("checkin", "<=", fields.Date.today())],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "byCheckout":
                subdomains = [
                    [("state", "in", ("onboard", "departure_delayed"))],
                    [("checkout", "=", fields.Date.today())],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "onBoard":
                subdomains = [
                    [("state", "in", ("onboard", "departure_delayed"))],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "toAssign":
                subdomains = [
                    [("to_assign", "=", True)],
                    [("state", "in", ("draft", "confirm", "arrival_delayed"))],
                    [("reservation_type", "!=", "out")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "cancelled":
                subdomains = [
                    [("state", "=", "cancel")],
                ]
                domain_filter.append(expression.AND(subdomains))
            elif folio_search_param.filterByState == "overbooking":
                subdomains = [
                    [("overbooking", "=", True)],
                ]
                domain_filter.append(expression.AND(subdomains))
        if domain_filter:
            domain = expression.AND([domain_fields, domain_filter[0]])
            if folio_search_param.filter and folio_search_param.filterByState:
                domain = expression.AND(
                    [domain_fields, domain_filter[0], domain_filter[1]]
                )
        else:
            domain = domain_fields
        result_folios = []
        reservations_result = (
            self.env["pms.reservation"].search(domain).mapped("folio_id").ids
        )
        PmsFolioShortInfo = self.env.datamodels["pms.folio.short.info"]
        for folio in self.env["pms.folio"].search(
            [("id", "in", reservations_result)],
            order=order_field,
            limit=folio_search_param.limit,
            offset=folio_search_param.offset,
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
                        "stateCode": reservation.state,
                        "cancelledReason": reservation.cancelled_reason
                        if reservation.cancelled_reason
                        else None,
                        "preferredRoomId": reservation.preferred_room_id.id
                        if reservation.preferred_room_id
                        else None,
                        "roomTypeId": reservation.room_type_id.id
                        if reservation.room_type_id
                        else None,
                        "roomTypeClassId": reservation.room_type_id.class_id.id
                        if reservation.room_type_id
                        else None,
                        "folioSequence": reservation.folio_sequence,
                        "adults": reservation.adults,
                        "priceTotal": reservation.price_total,
                        "pricelistId": reservation.pricelist_id.id
                        if reservation.pricelist_id
                        else None,
                        "saleChannelId": reservation.sale_channel_origin_id.id
                        if reservation.sale_channel_origin_id
                        else None,
                        "agencyId": reservation.agency_id.id
                        if reservation.agency_id
                        else None,
                        "isSplitted": reservation.splitted,
                        "toAssign": reservation.to_assign,
                        "reservationType": reservation.reservation_type,
                        "nights": reservation.nights,
                        "numServices": len(reservation.service_ids)
                        if reservation.service_ids
                        else 0,
                        "overbooking": reservation.overbooking,
                        "isReselling": any(
                            line.is_reselling
                            for line in reservation.reservation_line_ids
                        ),
                        "isBlocked": reservation.blocked,
                    }
                )
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
                    reservations=[] if not reservations else reservations,
                    paymentStateCode=folio.payment_state,
                    paymentStateDescription=dict(
                        folio.fields_get(["payment_state"])["payment_state"][
                            "selection"
                        ]
                    )[folio.payment_state],
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
                    createDate=folio.create_date.isoformat(),
                )
            )
        return result_folios

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/transactions",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.search.param"),
        output_param=Datamodel("pms.transaction.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_transactions(self, folio_id, pms_search_param):
        domain = list()
        domain.append(("id", "=", folio_id))
        if pms_search_param.pmsPropertyId:
            domain.append(("pms_property_id", "=", pms_search_param.pmsPropertyId))
        folio = self.env["pms.folio"].search(domain)
        transactions = []
        PmsTransactiontInfo = self.env.datamodels["pms.transaction.info"]
        if not folio:
            pass
        else:
            # if folio.payment_state == "not_paid":
            #     pass
            # else:
            if folio.payment_ids:
                for payment in folio.payment_ids.filtered(
                    lambda p: p.state == "posted"
                ):
                    payment._compute_pms_api_transaction_type()
                    transactions.append(
                        PmsTransactiontInfo(
                            id=payment.id,
                            amount=round(payment.amount, 2),
                            journalId=payment.journal_id.id,
                            date=datetime.combine(
                                payment.date, datetime.min.time()
                            ).isoformat(),
                            transactionType=payment.pms_api_transaction_type,
                            partnerId=payment.partner_id.id
                            if payment.partner_id
                            else None,
                            partnerName=payment.partner_id.name
                            if payment.partner_id
                            else None,
                            reference=payment.ref if payment.ref else None,
                            isReconcilied=(payment.reconciled_statements_count > 0),
                            downPaymentInvoiceId=payment.reconciled_invoice_ids.filtered(
                                lambda inv: inv._is_downpayment()
                            ),
                        )
                    )
        return transactions

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/charge",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.transaction.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_folio_charge(self, folio_id, pms_account_payment_info):
        folio = self.env["pms.folio"].browse(folio_id)
        partner_id = self.env["res.partner"].browse(pms_account_payment_info.partnerId)
        journal = self.env["account.journal"].browse(pms_account_payment_info.journalId)
        reservations = (
            self.env["pms.reservation"].browse(pms_account_payment_info.reservationIds)
            if pms_account_payment_info.reservationIds
            else False
        )
        if journal.type == "cash":
            # REVIEW: Temporaly, if not cash session open, create a new one automatically
            # Review this in pms_folio_service (/charge & /refund)
            # and in pms_transaction_service (POST)
            last_session = self._get_last_cash_session(journal_id=journal.id)
            if last_session.state != "open":
                self._action_open_cash_session(
                    pms_property_id=folio.pms_property_id.id,
                    amount=last_session.balance_end_real,
                    journal_id=journal.id,
                    force=False,
                )
        self.env["pms.folio"].do_payment(
            journal,
            journal.suspense_account_id,
            self.env.user,
            pms_account_payment_info.amount,
            folio,
            reservations=reservations,
            services=False,
            partner=partner_id,
            date=datetime.strptime(pms_account_payment_info.date, "%Y-%m-%d"),
        )
        folio_transactions = folio.payment_ids.filtered(
            lambda p: p.pms_api_transaction_type == "customer_inbound"
        )
        return folio_transactions.ids

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/refund",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.transaction.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_folio_refund(self, folio_id, pms_account_payment_info):
        folio = self.env["pms.folio"].browse(folio_id)
        partner_id = self.env["res.partner"].browse(pms_account_payment_info.partnerId)
        journal = self.env["account.journal"].browse(pms_account_payment_info.journalId)
        if journal.type == "cash":
            # REVIEW: Temporaly, if not cash session open, create a new one automatically
            # Review this in pms_folio_service (/charge & /refund)
            # and in pms_transaction_service (POST)
            last_session = self._get_last_cash_session(journal_id=journal.id)
            if last_session.state != "open":
                self._action_open_cash_session(
                    pms_property_id=folio.pms_property_id.id,
                    amount=last_session.balance_end_real,
                    journal_id=journal.id,
                    force=False,
                )
        self.env["pms.folio"].do_refund(
            journal,
            journal.suspense_account_id,
            self.env.user,
            pms_account_payment_info.amount,
            folio,
            reservations=False,
            services=False,
            partner=partner_id,
            date=datetime.strptime(pms_account_payment_info.date, "%Y-%m-%d"),
            ref=pms_account_payment_info.reference,
        )

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/reservations",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.reservation.short.info", is_list=True),
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
                for reservation in sorted(
                    folio.reservation_ids, key=lambda r: r.folio_sequence
                ):
                    reservations.append(
                        PmsReservationShortInfo(
                            id=reservation.id,
                            boardServiceId=reservation.board_service_room_id.id
                            if reservation.board_service_room_id
                            else None,
                            checkin=datetime.combine(
                                reservation.checkin, datetime.min.time()
                            ).isoformat(),
                            checkout=datetime.combine(
                                reservation.checkout, datetime.min.time()
                            ).isoformat(),
                            roomTypeId=reservation.room_type_id.id
                            if reservation.room_type_id
                            else None,
                            roomTypeClassId=reservation.room_type_id.class_id.id
                            if reservation.room_type_id
                            else None,
                            preferredRoomId=reservation.preferred_room_id.id
                            if reservation.preferred_room_id
                            else None,
                            name=reservation.name,
                            adults=reservation.adults,
                            stateCode=reservation.state,
                            stateDescription=dict(
                                reservation.fields_get(["state"])["state"]["selection"]
                            )[reservation.state],
                            children=reservation.children
                            if reservation.children
                            else 0,
                            readyForCheckin=reservation.ready_for_checkin,
                            allowedCheckout=reservation.allowed_checkout,
                            isSplitted=reservation.splitted,
                            priceTotal=round(reservation.price_room_services_set, 2),
                            folioSequence=reservation.folio_sequence
                            if reservation.folio_sequence
                            else None,
                            pricelistId=reservation.pricelist_id,
                            servicesCount=sum(
                                reservation.service_ids.filtered(
                                    lambda x: not x.is_board_service
                                ).mapped("product_qty")
                            ),
                            nights=reservation.nights,
                            numServices=len(reservation.service_ids)
                            if reservation.service_ids
                            else 0,
                            toAssign=reservation.to_assign,
                            overbooking=reservation.overbooking,
                            isBlocked=reservation.blocked,
                            reservationType=reservation.reservation_type,
                            segmentationId=reservation.segmentation_ids[0].id
                            if reservation.segmentation_ids
                            else None,
                        )
                    )

        return reservations

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.folio.info", is_list=False),
        auth="jwt_api_pms",
    )
    # flake8:noqa=C901
    def create_folio(self, pms_folio_info):
        external_app = self.env.user.pms_api_client
        log_payload = pms_folio_info
        min_checkin_payload = min(
            pms_folio_info.reservations, key=lambda x: x.checkin
        ).checkin
        max_checkout_payload = max(
            pms_folio_info.reservations, key=lambda x: x.checkout
        ).checkout
        try:
            agency = False
            if pms_folio_info.agencyId:
                agency = self.env["res.partner"].browse(pms_folio_info.agencyId)
            if pms_folio_info.reservationType == "out":
                vals = {
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "reservation_type": pms_folio_info.reservationType,
                    "closure_reason_id": pms_folio_info.closureReasonId,
                    "out_service_description": pms_folio_info.outOfServiceDescription
                    if pms_folio_info.outOfServiceDescription
                    else None,
                }
            else:
                vals = {
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "agency_id": agency.id if agency else False,
                    "sale_channel_origin_id": self.get_channel_origin_id(
                        pms_folio_info.saleChannelId, pms_folio_info.agencyId
                    ),
                    "reservation_type": pms_folio_info.reservationType or "normal",
                    "external_reference": pms_folio_info.externalReference,
                    "internal_comment": pms_folio_info.internalComment,
                    "lang": self.get_language(pms_folio_info.language),
                }

                if pms_folio_info.partnerId:
                    vals.update(
                        {
                            "partner_id": pms_folio_info.partnerId,
                        }
                    )
                else:
                    if pms_folio_info.partnerName:
                        vals.update(
                            {
                                "partner_name": pms_folio_info.partnerName,
                            }
                        )
                    if pms_folio_info.partnerPhone:
                        vals.update(
                            {
                                "mobile": pms_folio_info.partnerPhone,
                            }
                        )
                    if pms_folio_info.partnerEmail:
                        vals.update(
                            {
                                "email": pms_folio_info.partnerEmail,
                            }
                        )
            folio = self.env["pms.folio"].create(vals)
            for reservation in pms_folio_info.reservations:
                commision_percent_to_deduct = 0
                if external_app and agency and agency.commission_type == "subtract":
                    commision_percent_to_deduct = agency.default_commission
                vals = {
                    "folio_id": folio.id,
                    "room_type_id": reservation.roomTypeId,
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "pricelist_id": pms_folio_info.pricelistId,
                    "external_reference": pms_folio_info.externalReference or "normal",
                    "board_service_room_id": self.get_board_service_room_type_id(
                        reservation.boardServiceId,
                        reservation.roomTypeId,
                        pms_folio_info.pmsPropertyId,
                    ),
                    "preferred_room_id": reservation.preferredRoomId,
                    "adults": reservation.adults,
                    "reservation_type": pms_folio_info.reservationType or "normal",
                    "children": reservation.children,
                    "preconfirm": pms_folio_info.preconfirm,
                    "blocked": True if external_app else False,
                    "partner_requests": reservation.partnerRequests or "",
                }
                if reservation.reservationLines:
                    vals_lines = []
                    board_day_price = 0
                    # The service price is included in day price when it is a board service (external api)
                    if external_app and vals.get("board_service_room_id"):
                        board = self.env["pms.board.service.room.type"].browse(
                            vals["board_service_room_id"]
                        )
                        if reservation.adults:
                            board_day_price += (
                                sum(
                                    board.board_service_line_ids.with_context(
                                        property=folio.pms_property_id.id
                                    )
                                    .filtered(lambda l: l.adults)
                                    .mapped("amount")
                                )
                                * reservation.adults
                            )
                        if reservation.children:
                            board_day_price += (
                                sum(
                                    board.board_service_line_ids.with_context(
                                        property=folio.pms_property_id.id
                                    )
                                    .filtered(lambda l: l.children)
                                    .mapped("amount")
                                )
                                * reservation.children
                            )
                    for reservationLine in reservation.reservationLines:
                        price = reservationLine.price - (
                            commision_percent_to_deduct * reservationLine.price / 100
                        )
                        vals_lines.append(
                            (
                                0,
                                0,
                                {
                                    "date": reservationLine.date,
                                    "price": price - board_day_price,
                                    "discount": reservationLine.discount,
                                },
                            )
                        )
                    vals["reservation_line_ids"] = vals_lines
                else:
                    vals["checkin"] = reservation.checkin
                    vals["checkout"] = reservation.checkout

                reservation_record = (
                    self.env["pms.reservation"]
                    .with_context(
                        skip_compute_service_ids=False if external_app else True,
                        force_overbooking=True if external_app else False,
                        force_write_blocked=True if external_app else False,
                    )
                    .create(vals)
                )
                if reservation.services:
                    for service in reservation.services:
                        if service.serviceLines:
                            vals = {
                                "product_id": service.productId,
                                "reservation_id": reservation_record.id,
                                "is_board_service": service.isBoardService,
                                "service_line_ids": [
                                    (
                                        0,
                                        False,
                                        {
                                            "date": line.date,
                                            "price_unit": line.priceUnit,
                                            "discount": line.discount or 0,
                                            "day_qty": line.quantity,
                                        },
                                    )
                                    for line in service.serviceLines
                                ],
                            }
                            self.env["pms.service"].create(vals)
                        else:
                            product = self.env["product.product"].browse(
                                service.productId
                            )
                            vals = {
                                "product_id": service.productId,
                                "reservation_id": reservation_record.id,
                                "discount": service.discount or 0,
                            }
                            if not (product.per_day or product.per_person):
                                vals.update(
                                    {
                                        "product_qty": service.quantity,
                                    }
                                )
                            new_service = self.env["pms.service"].create(vals)
                            new_service.service_line_ids.price_unit = service.priceUnit
                # Force compute board service default if not board service is set
                # REVIEW: Precharge the board service in the app form?
                if (
                    not reservation_record.board_service_room_id
                    or reservation_record.board_service_room_id == 0
                ):
                    reservation_record.with_context(
                        skip_compute_service_ids=False,
                        force_write_blocked=True if external_app else False,
                    )._compute_board_service_room_id()
                if reservation.stateCode == "cancel":
                    reservation_record.action_cancel()
            pms_folio_info.transactions = self.normalize_payments_structure(
                pms_folio_info, folio
            )
            if pms_folio_info.transactions:
                self.compute_transactions(folio, pms_folio_info.transactions)
            if pms_folio_info.state == "cancel":
                folio.action_cancel()
            # REVIEW: analyze how to integrate the sending of mails from the API
            # with the configuration of the automatic mails pms
            # &
            # the sending of mail should be a specific call once the folio has been created?
            if folio and folio.email and pms_folio_info.sendConfirmationMail:
                template = folio.pms_property_id.property_confirmed_template
                if not template:
                    raise ValidationError(
                        _("There is no confirmation template for this property")
                    )
                email_values = {
                    "email_to": folio.email,
                    "email_from": folio.pms_property_id.email
                    if folio.pms_property_id.email
                    else False,
                    "auto_delete": False,
                }
                template.send_mail(folio.id, force_send=True, email_values=email_values)
            # Mapped room types and dates to call force_api_update_avail
            mapped_room_types = folio.reservation_ids.mapped("room_type_id")
            date_from = min(folio.reservation_ids.mapped("checkin"))
            date_to = max(folio.reservation_ids.mapped("checkout"))
            self.force_api_update_avail(
                pms_property_id=pms_folio_info.pmsPropertyId,
                room_type_ids=mapped_room_types.ids,
                date_from=date_from,
                date_to=date_to,
            )
            if external_app:
                self.env["pms.api.log"].sudo().create(
                    {
                        "pms_property_id": pms_folio_info.pmsPropertyId,
                        "client_id": self.env.user.id,
                        "request": log_payload,
                        "response": folio.id,
                        "status": "success",
                        "request_date": fields.Datetime.now(),
                        "method": "POST",
                        "endpoint": "/folios",
                        "folio_ids": folio.ids,
                        "target_date_from": min_checkin_payload,
                        "target_date_to": max_checkout_payload,
                        "request_type": "folios",
                    }
                )
            return folio.id
        except Exception as e:
            _logger.error(
                "Error creating folio from API: %s",
                e,
                exc_info=True,
            )
            self.env["pms.api.log"].sudo().create(
                {
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "client_id": self.env.user.id,
                    "request": log_payload,
                    "response": e,
                    "status": "error",
                    "request_date": fields.Datetime.now(),
                    "method": "POST",
                    "endpoint": "/folios",
                    "folio_ids": [],
                    "target_date_from": min_checkin_payload,
                    "target_date_to": max_checkout_payload,
                    "request_type": "folios",
                }
            )
            if not external_app:
                raise ValidationError(_("Error creating folio from API: %s") % e)
            else:
                return 0

    def compute_transactions(self, folio, transactions):
        for transaction in transactions:
            reference = folio.name + " - "
            if transaction.reference:
                reference += transaction.reference
            else:
                raise ValidationError(_("The transaction reference is required"))
            journal = self.env["account.journal"].search(
                [("id", "=", transaction.journalId)]
            )
            if not journal:
                ota_conf = self.env["ota.property.settings"].search(
                    [
                        ("pms_property_id", "=", folio.pms_property_id.id),
                        ("agency_id", "=", self.env.user.partner_id.id),
                    ]
                )
                if ota_conf:
                    journal = ota_conf.pms_api_payment_journal_id
            proposed_transaction = self.env["account.payment"].search(
                [
                    ("pms_property_id", "=", folio.pms_property_id.id),
                    ("payment_type", "=", transaction.transactionType),
                    ("folio_ids", "in", folio.id),
                    ("ref", "ilike", reference),
                    ("state", "=", "posted"),
                    ("create_uid", "=", self.env.user.id),
                    ("journal_id", "=", journal.id),
                ]
            )
            if (
                not proposed_transaction
                or proposed_transaction.amount != transaction.amount
            ):
                if proposed_transaction:
                    proposed_transaction.action_draft()
                    proposed_transaction.amount = transaction.amount
                    proposed_transaction.action_post()
                else:
                    if transaction.transactionType == "inbound":
                        folio.do_payment(
                            journal,
                            journal.suspense_account_id,
                            self.env.user,
                            transaction.amount,
                            folio,
                            reservations=False,
                            services=False,
                            partner=False,
                            date=datetime.strptime(transaction.date, "%Y-%m-%d"),
                            ref=reference,
                        )
                    elif transaction.transactionType == "outbound":
                        folio.do_refund(
                            journal,
                            journal.suspense_account_id,
                            self.env.user,
                            transaction.amount,
                            folio,
                            reservations=False,
                            services=False,
                            partner=False,
                            date=datetime.strptime(transaction.date, "%Y-%m-%d"),
                            ref=reference,
                        )

    @restapi.method(
        [
            (
                [
                    "/p/<int:folio_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.folio.info", is_list=False),
        auth="jwt_api_pms",
    )
    # flake8:noqa=C901
    def update_folio(self, folio_id, pms_folio_info):
        folio = self.env["pms.folio"].browse(folio_id)
        folio_vals = {}
        if not folio:
            raise MissingError(_("Folio not found"))
        if pms_folio_info.cancelReservations:
            folio.action_cancel()
        if pms_folio_info.confirmReservations:
            for reservation in folio.reservation_ids:
                reservation.action_confirm()
        if pms_folio_info.internalComment is not None:
            folio_vals.update({"internal_comment": pms_folio_info.internalComment})
        if pms_folio_info.partnerId:
            folio_vals.update({"partner_id": pms_folio_info.partnerId})
        else:
            if folio.partner_id:
                folio.partner_id = False
        if pms_folio_info.partnerName is not None:
            folio_vals.update({"partner_name": pms_folio_info.partnerName})
        if pms_folio_info.partnerEmail is not None:
            folio_vals.update({"email": pms_folio_info.partnerEmail})
        if pms_folio_info.partnerPhone is not None:
            folio_vals.update({"mobile": pms_folio_info.partnerPhone})
        if pms_folio_info.language:
            folio_vals.update({"lang": pms_folio_info.language})
        if pms_folio_info.reservations:
            for reservation in pms_folio_info.reservations:
                vals = {
                    "folio_id": folio.id,
                    "room_type_id": reservation.roomTypeId,
                    "checkin": reservation.checkin,
                    "checkout": reservation.checkout,
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "pricelist_id": pms_folio_info.pricelistId,
                    "external_reference": pms_folio_info.externalReference,
                    "board_service_room_id": reservation.boardServiceId,
                    "preferred_room_id": reservation.preferredRoomId,
                    "adults": reservation.adults,
                    "reservation_type": pms_folio_info.reservationType,
                    "children": reservation.children,
                }
                reservation_record = self.env["pms.reservation"].create(vals)
                if reservation.services:
                    for service in reservation.services:
                        vals = {
                            "product_id": service.productId,
                            "reservation_id": reservation_record.id,
                            "is_board_service": False,
                            "service_line_ids": [
                                (
                                    0,
                                    False,
                                    {
                                        "date": line.date,
                                        "price_unit": line.priceUnit,
                                        "discount": line.discount or 0,
                                        "day_qty": line.quantity,
                                    },
                                )
                                for line in service.serviceLines
                            ],
                        }
                        self.env["pms.service"].create(vals)
        if folio_vals:
            folio.write(folio_vals)

    # ------------------------------------------------------------------------------------
    # FOLIO SERVICES----------------------------------------------------------------
    # ------------------------------------------------------------------------------------

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/services",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.service.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_services(self, folio_id):
        folio = self.env["pms.folio"].search([("id", "=", folio_id)])
        if not folio:
            raise MissingError(_("Folio not found"))

        result_services = []
        PmsServiceInfo = self.env.datamodels["pms.service.info"]
        for reservation in folio.reservation_ids:
            for service in reservation.service_ids:
                PmsServiceLineInfo = self.env.datamodels["pms.service.line.info"]
                service_lines = []
                for line in service.service_line_ids:
                    service_lines.append(
                        PmsServiceLineInfo(
                            id=line.id,
                            date=datetime.combine(
                                line.date, datetime.min.time()
                            ).isoformat(),
                            priceUnit=line.price_unit,
                            discount=line.discount,
                            quantity=line.day_qty,
                        )
                    )

                result_services.append(
                    PmsServiceInfo(
                        id=service.id,
                        reservationId=service.reservation_id,
                        name=service.name,
                        productId=service.product_id.id,
                        quantity=service.product_qty,
                        priceTotal=round(service.price_total, 2),
                        priceSubtotal=round(service.price_subtotal, 2),
                        priceTaxes=round(service.price_tax, 2),
                        discount=round(service.discount, 2),
                        isBoardService=service.is_board_service,
                        serviceLines=service_lines,
                    )
                )
        return result_services

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/mail",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.mail.info"),
        output_param=Datamodel("pms.mail.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_folio_mail(self, folio_id, pms_mail_info):
        folio = self.env["pms.folio"].browse(folio_id)
        if pms_mail_info.mailType == "confirm":
            compose_vals = {
                "template_id": folio.pms_property_id.property_confirmed_template.id,
                "model": "pms.folio",
                "res_ids": folio.id,
            }
        elif pms_mail_info.mailType == "done":
            compose_vals = {
                "template_id": folio.pms_property_id.property_exit_template.id,
                "model": "pms.folio",
                "res_ids": folio.id,
            }
        elif pms_mail_info.mailType == "cancel":
            # TODO: only send first cancel reservation, not all
            # the template is not ready for multiple reservations
            compose_vals = {
                "template_id": folio.pms_property_id.property_canceled_template.id,
                "model": "pms.reservation",
                "res_ids": folio.reservation_ids.filtered(
                    lambda r: r.state == "cancel"
                )[0].id,
            }
        values = self.env["mail.compose.message"].generate_email_for_composer(
            template_id=compose_vals["template_id"],
            res_ids=compose_vals["res_ids"],
            fields=["subject", "body_html"],
        )
        PmsMailInfo = self.env.datamodels["pms.mail.info"]
        return PmsMailInfo(
            bodyMail=values["body"],
            subject=values["subject"],
        )

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/send-mail",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.mail.info"),
        auth="jwt_api_pms",
    )
    def send_folio_mail(self, folio_id, pms_mail_info):
        folio = self.env["pms.folio"].browse(folio_id)
        recipients = pms_mail_info.emailAddresses

        email_values = {
            "email_to": ",".join(recipients) if recipients else False,
            "partner_ids": pms_mail_info.partnerIds
            if pms_mail_info.partnerIds
            else False,
            "recipient_ids": pms_mail_info.partnerIds
            if pms_mail_info.partnerIds
            else False,
            "auto_delete": False,
        }
        if pms_mail_info.bodyMail:
            email_values.update(
                {
                    "body": pms_mail_info.bodyMail,
                    "body_html": pms_mail_info.bodyMail,
                }
            )
        if pms_mail_info.mailType == "confirm":
            template = folio.pms_property_id.property_confirmed_template
            res_id = folio.id
            template.send_mail(res_id, force_send=True, email_values=email_values)
        elif pms_mail_info.mailType == "done":
            template = folio.pms_property_id.property_exit_template
            res_id = folio.id
            template.send_mail(res_id, force_send=True, email_values=email_values)
        if pms_mail_info.mailType == "cancel":
            template = folio.pms_property_id.property_canceled_template
            res = folio.reservation_ids.filtered(lambda r: r.state == "cancel")
            res_id = res[0].id
            template.send_mail(res_id, force_send=True, email_values=email_values)
        return True

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/sale-lines",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.folio.sale.line.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_sale_lines(self, folio_id):
        folio = self.env["pms.folio"].browse(folio_id)
        sale_lines = []
        if not folio:
            pass
        else:
            PmsFolioSaleLineInfo = self.env.datamodels["pms.folio.sale.line.info"]
            if folio.sale_line_ids:
                for sale_line in folio.sale_line_ids:
                    sale_lines.append(
                        PmsFolioSaleLineInfo(
                            id=sale_line.id if sale_line.id else None,
                            name=sale_line.name if sale_line.name else None,
                            priceUnit=sale_line.price_unit
                            if sale_line.price_unit
                            else None,
                            qtyToInvoice=self._get_section_qty_to_invoice(sale_line)
                            if sale_line.display_type == "line_section"
                            else sale_line.qty_to_invoice,
                            qtyInvoiced=sale_line.qty_invoiced
                            if sale_line.qty_invoiced
                            else None,
                            priceTotal=sale_line.price_total
                            if sale_line.price_total
                            else None,
                            discount=sale_line.discount if sale_line.discount else None,
                            productQty=sale_line.product_uom_qty
                            if sale_line.product_uom_qty
                            else None,
                            reservationId=sale_line.reservation_id
                            if sale_line.reservation_id
                            else None,
                            serviceId=sale_line.service_id
                            if sale_line.service_id
                            else None,
                            displayType=sale_line.display_type
                            if sale_line.display_type
                            else None,
                            defaultInvoiceTo=sale_line.default_invoice_to
                            if sale_line.default_invoice_to
                            else None,
                            isDownPayment=sale_line.is_downpayment,
                        )
                    )

        return sale_lines

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/invoices",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.invoice.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_invoices(self, folio_id):
        folio = self.env["pms.folio"].browse(folio_id)
        invoices = []
        if not folio:
            pass
        else:
            PmsFolioInvoiceInfo = self.env.datamodels["pms.invoice.info"]
            PmsInvoiceLineInfo = self.env.datamodels["pms.invoice.line.info"]
            if folio.move_ids:
                for move in folio.move_ids:
                    move_lines = []
                    for move_line in move.invoice_line_ids:
                        move_lines.append(
                            PmsInvoiceLineInfo(
                                id=move_line.id,
                                name=move_line.name if move_line.name else None,
                                quantity=move_line.quantity
                                if move_line.quantity
                                else None,
                                priceUnit=move_line.price_unit
                                if move_line.price_unit
                                else None,
                                total=move_line.price_total
                                if move_line.price_total
                                else None,
                                discount=move_line.discount
                                if move_line.discount
                                else None,
                                displayType=move_line.display_type
                                if move_line.display_type
                                else None,
                                saleLineId=move_line.folio_line_ids[0]
                                if move_line.folio_line_ids
                                else None,
                                isDownPayment=move_line.move_id._is_downpayment(),
                            )
                        )
                    move_url = (
                        move.get_proforma_portal_url()
                        if move.state == "draft"
                        else move.get_portal_url()
                    )
                    portal_url = (
                        self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                        + move_url
                    )
                    invoice_date = (
                        move.invoice_date.strftime("%d/%m/%Y")
                        if move.invoice_date
                        else move.invoice_date_due.strftime("%d/%m/%Y")
                        if move.invoice_date_due
                        else None
                    )
                    invoices.append(
                        PmsFolioInvoiceInfo(
                            id=move.id if move.id else None,
                            name=move.name if move.name else None,
                            amount=round(move.amount_total, 2)
                            if move.amount_total
                            else None,
                            date=invoice_date,
                            state=move.state if move.state else None,
                            paymentState=move.payment_state
                            if move.payment_state
                            else None,
                            partnerName=move.partner_id.name
                            if move.partner_id.name
                            else None,
                            partnerId=move.partner_id.id
                            if move.partner_id.id
                            else None,
                            moveLines=move_lines if move_lines else None,
                            portalUrl=portal_url,
                            moveType=move.move_type,
                            isReversed=move.payment_state == "reversed",
                            isDownPaymentInvoice=move._is_downpayment(),
                            isSimplifiedInvoice=move.journal_id.is_simplified_invoice,
                            narration=move.narration if move.narration else None,
                        )
                    )
        return invoices

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/invoices",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.invoice.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_folio_invoices(self, folio_id, invoice_info):
        # TODO: Missing payload data:
        # - date format is in invoice_info but dont save
        # - invoice comment is in invoice_info but dont save
        lines_to_invoice_dict = dict()
        if not invoice_info.partnerId:
            raise MissingError(_("For manual invoice, partner is required"))
        for item in invoice_info.saleLines:
            if item.qtyToInvoice:
                lines_to_invoice_dict[item.id] = item.qtyToInvoice

        sale_lines_to_invoice = self.env["folio.sale.line"].browse(
            lines_to_invoice_dict.keys()
        )
        for line in sale_lines_to_invoice:
            if line.section_id and line.section_id.id not in sale_lines_to_invoice.ids:
                sale_lines_to_invoice |= line.section_id
                lines_to_invoice_dict[line.section_id.id] = 0
        folios_to_invoice = sale_lines_to_invoice.folio_id
        invoices = folios_to_invoice._create_invoices(
            lines_to_invoice=lines_to_invoice_dict,
            partner_invoice_id=invoice_info.partnerId,
            final=True,  # To force take into account down payments
        )
        # TODO: Proposed improvement with strong refactoring:
        # modify the folio _create_invoices() method so that it allows specifying any
        # lines field before creation (right now it only allows quantity),
        # avoiding having to review the lines to modify them afterwards
        for item in invoice_info.saleLines:
            if item.id in invoices.invoice_line_ids.mapped("folio_line_ids.id"):
                invoice_line = invoices.invoice_line_ids.filtered(
                    lambda r: item.id in r.folio_line_ids.ids
                    and not any([r.folio_line_ids.is_downpayment])
                    # To avoid modifying down payments description
                )
                if invoice_line:
                    invoice_line.write({"name": item.name})
        if invoice_info.narration:
            invoices.write({"narration": invoice_info.narration})
        return invoices.ids

    # TODO: Used for the temporary function of auto-open cash session
    # (View: charge/refund endpoints)
    def _get_last_cash_session(self, journal_id, pms_property_id=False):
        domain = [("journal_id", "=", journal_id)]
        if pms_property_id:
            domain.append(("pms_property_id", "=", pms_property_id))
        return (
            self.env["account.bank.statement"]
            .sudo()
            .search(
                domain,
                order="date desc, id desc",
                limit=1,
            )
        )

    # TODO: Used for the temporary function of auto-open cash session
    # (View: charge/refund endpoints))
    def _action_open_cash_session(self, pms_property_id, amount, journal_id, force):
        statement = self._get_last_cash_session(
            journal_id=journal_id,
            pms_property_id=pms_property_id,
        )
        if round(statement.balance_end_real, 2) == round(amount, 2) or force:
            self.env["account.bank.statement"].sudo().create(
                {
                    "name": datetime.today().strftime(get_lang(self.env).date_format)
                    + " ("
                    + self.env.user.login
                    + ")",
                    "date": datetime.today(),
                    "balance_start": amount,
                    "journal_id": journal_id,
                    "pms_property_id": pms_property_id,
                }
            )
            diff = round(amount - statement.balance_end_real, 2)
            return {"result": True, "diff": diff}
        else:
            diff = round(amount - statement.balance_end_real, 2)
            return {"result": False, "diff": diff}

    def _get_section_qty_to_invoice(self, sale_line):
        folio = sale_line.folio_id
        if sale_line.display_type == "line_section":
            # Get if the section has a lines to invoice
            seq = sale_line.sequence
            next_line_section = folio.sale_line_ids.filtered(
                lambda l: l.sequence > seq and l.display_type == "line_section"
            )
            if next_line_section:
                return sum(
                    folio.sale_line_ids.filtered(
                        lambda l: l.sequence > seq
                        and l.sequence < next_line_section[0].sequence
                        and l.display_type != "line_section"
                    ).mapped("qty_to_invoice")
                )
            else:
                return sum(
                    folio.sale_line_ids.filtered(
                        lambda l: l.sequence > seq and l.display_type != "line_section"
                    ).mapped("qty_to_invoice")
                )
        return 0

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/checkin-partners",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.checkin.partner.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_checkin_partners(self, folio_id):
        folio = self.env["pms.folio"].browse(folio_id)
        checkin_partners = []
        if folio:
            PmsCheckinPartnerInfo = self.env.datamodels["pms.checkin.partner.info"]
            for checkin_partner in folio.checkin_partner_ids:
                checkin_partners.append(
                    PmsCheckinPartnerInfo(
                        id=checkin_partner.id,
                        reservationId=checkin_partner.reservation_id.id,
                        name=checkin_partner.name if checkin_partner.name else "",
                        firstname=checkin_partner.firstname
                        if checkin_partner.firstname
                        else None,
                        lastname=checkin_partner.lastname
                        if checkin_partner.lastname
                        else None,
                        lastname2=checkin_partner.lastname2
                        if checkin_partner.lastname2
                        else None,
                        email=checkin_partner.email if checkin_partner.email else "",
                        mobile=checkin_partner.mobile if checkin_partner.mobile else "",
                        documentType=checkin_partner.document_type.id
                        if checkin_partner.document_type
                        else None,
                        documentNumber=checkin_partner.document_number
                        if checkin_partner.document_number
                        else None,
                        documentExpeditionDate=datetime.combine(
                            checkin_partner.document_expedition_date,
                            datetime.min.time(),
                        ).isoformat()
                        if checkin_partner.document_expedition_date
                        else None,
                        documentSupportNumber=checkin_partner.support_number
                        if checkin_partner.support_number
                        else None,
                        documentCountryId=checkin_partner.document_country_id.id
                        if checkin_partner.document_country_id
                        else None,
                        gender=checkin_partner.gender if checkin_partner.gender else "",
                        birthdate=datetime.combine(
                            checkin_partner.birthdate_date, datetime.min.time()
                        ).isoformat()
                        if checkin_partner.birthdate_date
                        else None,
                        residenceStreet=checkin_partner.residence_street
                        if checkin_partner.residence_street
                        else None,
                        zip=checkin_partner.residence_zip
                        if checkin_partner.residence_zip
                        else None,
                        residenceCity=checkin_partner.residence_city
                        if checkin_partner.residence_city
                        else None,
                        nationality=checkin_partner.nationality_id.id
                        if checkin_partner.nationality_id
                        else None,
                        countryState=checkin_partner.residence_state_id.id
                        if checkin_partner.residence_state_id
                        else None,
                        countryStateName=checkin_partner.residence_state_id.name
                        if checkin_partner.residence_state_id
                        else None,
                        countryId=checkin_partner.residence_country_id.id
                        if checkin_partner.residence_country_id
                        else None,
                        checkinPartnerState=checkin_partner.state,
                        signature=checkin_partner.signature
                        if checkin_partner.signature
                        else None,
                    )
                )
        return checkin_partners

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>/messages",
                ],
                "GET",
            )
        ],
        auth="jwt_api_pms",
        output_param=Datamodel("pms.message.info", is_list=False),
    )
    def get_folio_reservation_messages(self, folio_id):
        reservation_messages = []
        folio_messages = []
        if folio_id:
            folio = self.env["pms.folio"].browse(folio_id)
            reservations = self.env["pms.reservation"].browse(folio.reservation_ids.ids)
            user_tz = pytz.timezone(self.env.user.tz)
            for messages in reservations.message_ids:
                PmsReservationMessageInfo = self.env.datamodels[
                    "pms.reservation.message.info"
                ]
                for message in messages:
                    reservation_message_date = pytz.UTC.localize(message.date)
                    reservation_message_date = reservation_message_date.astimezone(
                        user_tz
                    )
                    message_body = self.parse_message_body(message)
                    if message.message_type == "email":
                        subject = "Email enviado: " + message.subject
                    else:
                        subject = message.subject if message.subject else None
                    reservation_messages.append(
                        PmsReservationMessageInfo(
                            reservationId=message.res_id,
                            author=message.author_id.name
                            if message.author_id
                            else message.email_from,
                            message=message_body,
                            subject=subject,
                            date=reservation_message_date.strftime("%d/%m/%y %H:%M:%S"),
                            messageType=message.message_type,
                            authorImageBase64=base64.b64encode(
                                message.author_id.image_1024
                            ).decode("utf-8")
                            if message.author_id.image_1024
                            else None,
                            authorImageUrl=url_image_pms_api_rest(
                                "res.partner", message.author_id.id, "image_1024"
                            ),
                        )
                    )
            PmsFolioMessageInfo = self.env.datamodels["pms.folio.message.info"]
            for folio_message in folio.message_ids:
                message_body = self.parse_message_body(folio_message)
                if folio_message.message_type == "email":
                    subject = "Email enviado: " + folio_message.subject
                else:
                    subject = folio_message.subject if folio_message.subject else None
                folio_message_date = pytz.UTC.localize(folio_message.date)
                folio_message_date = folio_message_date.astimezone(user_tz)
                folio_messages.append(
                    PmsFolioMessageInfo(
                        author=folio_message.author_id.name
                        if folio_message.author_id
                        else folio_message.email_from,
                        message=message_body,
                        subject=subject,
                        date=folio_message_date.strftime("%d/%m/%y %H:%M:%S"),
                        messageType=folio_message.message_type,
                        authorImageBase64=base64.b64encode(
                            folio_message.author_id.image_1024
                        ).decode("utf-8")
                        if folio_message.author_id.image_1024
                        else None,
                        authorImageUrl=url_image_pms_api_rest(
                            "res.partner", folio_message.author_id.id, "image_1024"
                        ),
                    )
                )
            PmsMessageInfo = self.env.datamodels["pms.message.info"]
            return PmsMessageInfo(
                folioMessages=folio_messages,
                reservationMessages=reservation_messages,
            )

    def parse_message_body(self, message):
        message = message.sudo()
        message_body = ""
        if message.body:
            message_body = message.body
        elif message.tracking_value_ids:
            old_value = False
            new_value = False
            for tracking_value in message.tracking_value_ids:
                if tracking_value.field_type == "float":
                    old_value = tracking_value.old_value_float
                    new_value = tracking_value.new_value_float
                elif (
                    tracking_value.field_type == "char"
                    or tracking_value.field_type == "selection"
                    or tracking_value.field_type == "many2one"
                ):
                    old_value = tracking_value.old_value_char
                    new_value = tracking_value.new_value_char
                elif tracking_value.field_type == "datetime":
                    old_value = tracking_value.old_value_datetime
                    new_value = tracking_value.new_value_datetime
                elif tracking_value.field_type == "integer":
                    old_value = tracking_value.old_value_integer
                    new_value = tracking_value.new_value_integer
                elif tracking_value.field_type == "monetary":
                    old_value = tracking_value.old_value_monetary
                    new_value = tracking_value.new_value_monetary
                elif tracking_value.field_type == "text":
                    old_value = tracking_value.old_value_text
                    new_value = tracking_value.new_value_text
                message_body += (
                    "-"
                    + tracking_value.field.field_description
                    + ": "
                    + str(old_value)
                    + " => "
                    + str(new_value)
                )
        return message_body

    def get_channel_origin_id(self, sale_channel_id, agency_id):
        """
        Returns the channel origin id for the given agency
        or website channel if not agency is given
        (TODO change by configuration user api in the future)
        """
        external_app = self.env.user.pms_api_client
        if sale_channel_id:
            return sale_channel_id
        if not agency_id and external_app:
            channel_origin_id = (
                self.env.user.partner_id.sale_channel_id.id
                if self.env.user.partner_id.sale_channel_id
                else self.env["pms.sale.channel"]
                .search(
                    [("channel_type", "=", "direct"), ("is_on_line", "=", True)],
                    limit=1,
                )
                .id
            )
            return channel_origin_id
        agency = self.env["res.partner"].browse(agency_id)
        if agency:
            return agency.sale_channel_id.id
        return False

    def get_language(self, lang_code):
        """
        Returns the language for the given language code
        """
        external_app = self.env.user.pms_api_client
        if not external_app:
            return lang_code
        return self.env["res.lang"].search([("iso_code", "=", lang_code)], limit=1).code

    def get_board_service_room_type_id(
        self, board_service_id, room_type_id, pms_property_id
    ):
        """
        The internal app uses the board service room type id to create the reservation,
        but the external app uses the board service id and the room type id.
        Returns the board service room type id for the given board service and room type
        """
        board_service = self.env["pms.board.service"].browse(board_service_id)
        room_type = self.env["pms.room.type"].browse(room_type_id)
        external_app = self.env.user.pms_api_client
        if not external_app:
            return board_service_id
        if board_service and room_type:
            return (
                self.env["pms.board.service.room.type"]
                .search(
                    [
                        ("pms_board_service_id", "=", board_service.id),
                        ("pms_room_type_id", "=", room_type.id),
                        ("pms_property_id", "=", pms_property_id),
                    ],
                    limit=1,
                )
                .id
            )
        return False

    # TEMP

    @restapi.method(
        [
            (
                [
                    "/external/<string:external_reference>",
                ],
                "PUT",
            )
        ],
        input_param=Datamodel("pms.folio.info", is_list=False),
        auth="jwt_api_pms",
    )
    def update_put_external_folio(self, external_reference, pms_folio_info):
        external_app = self.env.user.pms_api_client
        log_payload = pms_folio_info
        min_checkin_payload = min(
            pms_folio_info.reservations, key=lambda x: x.checkin
        ).checkin
        max_checkout_payload = max(
            pms_folio_info.reservations, key=lambda x: x.checkout
        ).checkout
        try:
            folio = self.env["pms.folio"].search(
                [
                    ("external_reference", "ilike", external_reference),
                    ("pms_property_id", "=", pms_folio_info.pmsPropertyId),
                ]
            )
            if not folio or len(folio) > 1:
                raise MissingError(_("Folio not found"))
            self.update_folio_values(folio, pms_folio_info)
            # Force update availability
            mapped_room_types = folio.reservation_ids.mapped("room_type_id")
            date_from = min(folio.reservation_ids.mapped("checkin"))
            date_to = max(folio.reservation_ids.mapped("checkout"))
            self.force_api_update_avail(
                pms_property_id=pms_folio_info.pmsPropertyId,
                room_type_ids=mapped_room_types.ids,
                date_from=date_from,
                date_to=date_to,
            )
            self.env["pms.api.log"].sudo().create(
                {
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "client_id": self.env.user.id,
                    "request": log_payload,
                    "response": folio.id,
                    "status": "success",
                    "request_date": fields.Datetime.now(),
                    "method": "PUT",
                    "endpoint": "/folios/external/" + external_reference,
                    "folio_ids": folio.ids,
                    "target_date_from": min_checkin_payload,
                    "target_date_to": max_checkout_payload,
                    "request_type": "folios",
                }
            )
            return folio.id
        except Exception as e:
            _logger.error(
                "Error updating folio from API: %s",
                e,
                exc_info=True,
            )
            self.env["pms.api.log"].sudo().create(
                {
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "client_id": self.env.user.id,
                    "request": log_payload,
                    "response": e,
                    "status": "error",
                    "request_date": fields.Datetime.now(),
                    "method": "PUT",
                    "endpoint": "/folios/external/" + external_reference,
                    "folio_ids": [],
                    "target_date_from": min_checkin_payload,
                    "target_date_to": max_checkout_payload,
                    "request_type": "folios",
                }
            )
            if not external_app:
                raise ValidationError(_("Error updating folio from API: %s") % e)
            else:
                return 0

    @restapi.method(
        [
            (
                [
                    "/<int:folio_id>",
                ],
                "PUT",
            )
        ],
        input_param=Datamodel("pms.folio.info", is_list=False),
        auth="jwt_api_pms",
    )
    def update_put_folio(self, folio_id, pms_folio_info):
        external_app = self.env.user.pms_api_client
        log_payload = pms_folio_info
        min_checkin_payload = min(
            pms_folio_info.reservations, key=lambda x: x.checkin
        ).checkin
        max_checkout_payload = max(
            pms_folio_info.reservations, key=lambda x: x.checkout
        ).checkout
        try:
            folio = self.env["pms.folio"].browse(folio_id)
            if not folio:
                raise MissingError(_("Folio not found"))
            self.update_folio_values(folio, pms_folio_info)
            # Force update availability
            mapped_room_types = folio.reservation_ids.mapped("room_type_id")
            date_from = min(folio.reservation_ids.mapped("checkin"))
            date_to = max(folio.reservation_ids.mapped("checkout"))
            self.force_api_update_avail(
                pms_property_id=pms_folio_info.pmsPropertyId,
                room_type_ids=mapped_room_types.ids,
                date_from=date_from,
                date_to=date_to,
            )
            self.env["pms.api.log"].sudo().create(
                {
                    "pms_property_id": pms_folio_info.pmsPropertyId,
                    "client_id": self.env.user.id,
                    "request": log_payload,
                    "response": folio.id,
                    "status": "success",
                    "request_date": fields.Datetime.now(),
                    "method": "PUT",
                    "endpoint": "/folios" + str(folio_id),
                    "folio_ids": folio.ids,
                    "target_date_from": min_checkin_payload,
                    "target_date_to": max_checkout_payload,
                    "request_type": "folios",
                }
            )

            return folio.id
        except Exception as e:
            _logger.error(
                "Error updating folio from API: %s",
                e,
                exc_info=True,
            )
            self.env["pms.api.log"].sudo().create(
                {
                    "pms_property_id": log_payload.pmsPropertyId,
                    "client_id": self.env.user.id,
                    "request": log_payload,
                    "response": e,
                    "status": "error",
                    "request_date": fields.Datetime.now(),
                    "method": "PUT",
                    "endpoint": "/folios" + str(folio_id),
                    "folio_ids": [],
                    "target_date_from": min_checkin_payload,
                    "target_date_to": max_checkout_payload,
                    "request_type": "folios",
                }
            )
            if not external_app:
                raise ValidationError(_("Error updating folio from API: %s") % e)
            else:
                return 0

    def update_folio_values(self, folio, pms_folio_info):
        external_app = self.env.user.pms_api_client
        folio_vals = {}
        if pms_folio_info.state == "cancel" and folio.state != "cancel":
            draft_invoices = folio.move_ids.filtered(lambda i: i.state == "draft")
            if draft_invoices:
                draft_invoices.button_cancel()
            folio.action_cancel()
            return folio.id
        # if (
        #     pms_folio_info.confirmReservations
        #     and any(
        #         reservation.state != "confirm"
        #         for reservation in folio.reservation_ids
        #     )
        # ):
        #     for reservation in folio.reservation_ids:
        #         reservation.action_confirm()
        if (
            pms_folio_info.internalComment is not None
            and pms_folio_info.internalComment not in folio.internal_comment
        ):
            folio_vals.update(
                {
                    "internal_comment": folio.internal_comment
                    + " "
                    + pms_folio_info.internalComment
                }
            )
        if pms_folio_info.partnerId and folio.partner_id.id != pms_folio_info.partnerId:
            folio_vals.update({"partner_id": pms_folio_info.partnerId})
        elif not pms_folio_info.partnerId:
            if folio.partner_id:
                folio.partner_id = False
        if (
            pms_folio_info.partnerName is not None
            and folio.partner_name != pms_folio_info.partnerName
        ):
            folio_vals.update({"partner_name": pms_folio_info.partnerName})
        if (
            pms_folio_info.partnerEmail is not None
            and folio.email != pms_folio_info.partnerEmail
        ):
            folio_vals.update({"email": pms_folio_info.partnerEmail})
        if (
            pms_folio_info.partnerPhone is not None
            and folio.mobile != pms_folio_info.partnerPhone
        ):
            folio_vals.update({"mobile": pms_folio_info.partnerPhone})
        if (
            self.get_language(pms_folio_info.language)
            and self.get_language(pms_folio_info.language) != folio.lang
        ):
            folio_vals.update({"lang": self.get_language(pms_folio_info.language)})
        reservations_vals = []
        if pms_folio_info.reservations:
            reservations_vals = self.wrapper_reservations(
                folio, pms_folio_info.reservations
            )
            if reservations_vals:
                update_reservation_ids = []
                for val in reservations_vals:
                    # Cancel the old reservations that have not been included in the update
                    if val[0] == 1:
                        if val[2].get("state") == "cancel":
                            self.env["pms.reservation"].with_context(
                                force_write_blocked=True
                            ).browse(val[1]).action_cancel()
                            # delete from reservations_vals the reservation that has been canceled
                            reservations_vals.pop(reservations_vals.index(val))
                        if val[2].get("state") == "confirm":
                            self.env["pms.reservation"].with_context(
                                force_write_blocked=True,
                                force_overbooking=True if external_app else False,
                            ).browse(val[1]).action_confirm()
                            # delete from reservations_vals the field state
                            val[2].pop("state")
                        update_reservation_ids.append(val[1])
                old_reservations_to_cancel = folio.reservation_ids.filtered(
                    lambda r: r.state != "cancel" and r.id not in update_reservation_ids
                )
                old_reservations_to_cancel.with_context(
                    modified=True, force_write_blocked=True
                ).action_cancel()
                folio_vals.update({"reservation_ids": reservations_vals})
        if folio_vals:
            folio.with_context(
                skip_compute_service_ids=False if external_app else True,
                force_overbooking=True if external_app else False,
                force_write_blocked=True if external_app else False,
            ).write(folio_vals)
        # Compute OTA transactions
        pms_folio_info.transactions = self.normalize_payments_structure(
            pms_folio_info, folio
        )
        if pms_folio_info.transactions:
            self.compute_transactions(folio, pms_folio_info.transactions)

    def normalize_payments_structure(self, pms_folio_info, folio):
        """
        This method use the OTA payment structure to normalize the structure
        and incorporate them in the transactions datamodel param
        """
        if pms_folio_info.transactions:
            # If the payment issuer is the API client, the payment will come in transactions
            # if not, we will have to look in the payload for the
            # payment identifier configured in the OTA
            for transaction in pms_folio_info.transactions:
                if not transaction.journalId:
                    ota_conf = self.env["ota.property.settings"].search(
                        [
                            ("pms_property_id", "=", pms_folio_info.pmsPropertyId),
                            ("agency_id", "=", self.env.user.partner_id.id),
                        ]
                    )
                    if not ota_conf:
                        raise ValidationError(
                            _("No OTA configuration found for this property")
                        )
                    if not ota_conf.pms_api_payment_journal_id:
                        raise ValidationError(
                            _(
                                "No payment journal configured for this property for %s"
                                % ota_conf.name
                            )
                        )
                    transaction.journalId = ota_conf.pms_api_payment_journal_id.id
        elif pms_folio_info.agencyId:
            ota_conf = self.env["ota.property.settings"].search(
                [
                    ("pms_property_id", "=", pms_folio_info.pmsPropertyId),
                    ("agency_id", "=", pms_folio_info.agencyId),
                ]
            )
            # Compute amount total like the sum of the price in reservation lines
            # and the sum of the price in service lines in the pms_folio_info
            amount_total = 0
            for reservation in pms_folio_info.reservations:
                if reservation.reservationLines:
                    amount_total += sum(
                        [
                            line.price - (line.price * ((line.discount or 0.0) * 0.01))
                            for line in reservation.reservationLines
                            if line.price
                        ]
                    )
                if reservation.services:
                    amount_total += sum(
                        [
                            service.priceUnit * service.quantity
                            for service in reservation.services
                            if service.priceUnit and service.quantity
                        ]
                    )

            # TODO: Review where to input the data to identify payments,
            # as partnerRequest in the reservation doesn't seem like the best location.
            if (
                ota_conf
                and ota_conf.pms_api_alowed_payments
                and any(
                    [
                        reservation.partnerRequests
                        and ota_conf.pms_api_payment_identifier
                        in reservation.partnerRequests
                        for reservation in pms_folio_info.reservations
                    ]
                )
            ):
                journal = ota_conf.pms_api_payment_journal_id
                pmsTransactionInfo = self.env.datamodels["pms.transaction.info"]
                pms_folio_info.transactions = [
                    pmsTransactionInfo(
                        journalId=journal.id,
                        transactionType="inbound",
                        amount=round(amount_total, 2),
                        date=fields.Date.today().strftime("%Y-%m-%d"),
                        reference=pms_folio_info.externalReference,
                    )
                ]
        return pms_folio_info.transactions

    def wrapper_reservations(self, folio, info_reservations):
        """
        This method is used to create or update the reservations in folio
        We try to find the reservation in the folio, if it exists we update it
        if not we create it
        To find the reservation we compare the number of reservations and try
        To return a list of ids with resevations to cancel by modification
        """
        external_app = self.env.user.pms_api_client
        cmds = []
        saved_reservations = folio.reservation_ids
        agency = folio.agency_id
        commision_percent_to_deduct = 0
        if external_app and agency and agency.commission_type == "subtract":
            commision_percent_to_deduct = agency.default_commission
        for info_reservation in info_reservations:
            # Search a reservation in saved_reservations whose sum of night amounts is equal
            # to the sum of night amounts of info_reservation, and dates equal,
            # if we find it we update it
            proposed_reservation = saved_reservations.filtered(
                lambda r: r.checkin
                == datetime.strptime(info_reservation.checkin, "%Y-%m-%d").date()
                and r.checkout
                == datetime.strptime(info_reservation.checkout, "%Y-%m-%d").date()
                and r.room_type_id.id == info_reservation.roomTypeId
                and r.adults == info_reservation.adults
                and r.children == info_reservation.children
            )
            if proposed_reservation:
                proposed_reservation = proposed_reservation[0]
                saved_reservations -= proposed_reservation
            vals = {}
            new_res = not proposed_reservation
            if new_res:
                vals.update({"folio_id": folio.id})
            if info_reservation.roomTypeId:
                if (
                    new_res
                    or proposed_reservation.room_type_id.id
                    != info_reservation.roomTypeId
                ):
                    vals.update({"room_type_id": info_reservation.roomTypeId})
            if info_reservation.checkin:
                if (
                    new_res
                    or proposed_reservation.checkin
                    != datetime.strptime(info_reservation.checkin, "%Y-%m-%d").date()
                ):
                    vals.update({"checkin": info_reservation.checkin})
            if info_reservation.checkout:
                if (
                    new_res
                    or proposed_reservation.checkout
                    != datetime.strptime(info_reservation.checkout, "%Y-%m-%d").date()
                ):
                    vals.update({"checkout": info_reservation.checkout})
            if info_reservation.pricelistId:
                if (
                    new_res
                    or proposed_reservation.pricelist_id.id
                    != info_reservation.pricelistId
                ):
                    vals.update({"pricelist_id": info_reservation.pricelistId})
            if info_reservation.boardServiceId:
                board_service_id = self.get_board_service_room_type_id(
                    info_reservation.boardServiceId,
                    info_reservation.roomTypeId,
                    folio.pms_property_id.id,
                )
                if (
                    new_res
                    or proposed_reservation.board_service_room_id.id != board_service_id
                ):
                    vals.update({"board_service_room_id": board_service_id})
            if info_reservation.preferredRoomId:
                if (
                    new_res
                    or proposed_reservation.preferred_room_id.id
                    != info_reservation.preferredRoomId
                ):
                    vals.update({"preferred_room_id": info_reservation.preferredRoomId})
            if info_reservation.partnerRequests:
                if (
                    new_res
                    or proposed_reservation.partner_requests
                    != info_reservation.partnerRequests
                ):
                    vals.update({"partner_requests": info_reservation.partnerRequests})
            if info_reservation.adults:
                if new_res or proposed_reservation.adults != info_reservation.adults:
                    vals.update({"adults": info_reservation.adults})
            if info_reservation.children:
                if (
                    new_res
                    or proposed_reservation.children != info_reservation.children
                ):
                    vals.update({"children": info_reservation.children})
            if new_res or info_reservation.stateCode != proposed_reservation.state:
                vals.update({"state": info_reservation.stateCode})
            if info_reservation.reservationLines:
                # The service price is included in day price when it is a board service (external api)
                board_day_price = 0
                if external_app and info_reservation.boardServiceId:
                    board = self.env["pms.board.service.room.type"].browse(
                        self.get_board_service_room_type_id(
                            info_reservation.boardServiceId,
                            info_reservation.roomTypeId,
                            folio.pms_property_id.id,
                        )
                    )
                    if info_reservation.adults:
                        board_day_price += (
                            sum(
                                board.board_service_line_ids.with_context(
                                    property=folio.pms_property_id.id
                                )
                                .filtered(lambda l: l.adults)
                                .mapped("amount")
                            )
                            * info_reservation.adults
                        )
                    if info_reservation.children:
                        board_day_price += (
                            sum(
                                board.board_service_line_ids.with_context(
                                    property=folio.pms_property_id.id
                                )
                                .filtered(lambda l: l.children)
                                .mapped("amount")
                            )
                            * info_reservation.children
                        )
                reservation_lines_cmds = self.wrapper_reservation_lines(
                    reservation=info_reservation,
                    board_day_price=board_day_price,
                    proposed_reservation=proposed_reservation,
                    commission_percent_to_deduct=commision_percent_to_deduct,
                )
                if reservation_lines_cmds:
                    vals.update({"reservation_line_ids": reservation_lines_cmds})
            if info_reservation.services:
                reservation_services_cmds = self.wrapper_reservation_services(
                    info_services=info_reservation.services,
                    services=proposed_reservation.service_ids
                    if proposed_reservation
                    else False,
                )
                if reservation_services_cmds:
                    vals.update({"service_ids": reservation_services_cmds})
            if not vals:
                continue
            elif new_res:
                cmds.append((0, False, vals))
            else:
                cmds.append((1, proposed_reservation.id, vals))
        return cmds

    def wrapper_reservation_lines(
        self,
        reservation,
        board_day_price=0,
        proposed_reservation=False,
        commission_percent_to_deduct=0,
    ):
        cmds = []
        for line in reservation.reservationLines:
            if proposed_reservation:
                # Not is necesay check new dates, becouse a if the dates change, the reservation is new
                proposed_line = proposed_reservation.reservation_line_ids.filtered(
                    lambda l: l.date == datetime.strptime(line.date, "%Y-%m-%d").date()
                )
                line.price -= commission_percent_to_deduct * proposed_line.price / 100
                if proposed_line:
                    vals = {}
                    if round(proposed_line.price, 2) != round(
                        line.price - board_day_price, 2
                    ):
                        vals.update({"price": line.price - board_day_price})
                    if round(proposed_line.discount, 2) != round(line.discount, 2):
                        vals.update({"discount": line.discount})
                    if vals:
                        cmds.append((1, proposed_line.id, vals))
                else:
                    cmds.append(
                        (
                            0,
                            False,
                            {
                                "date": line.date,
                                "price": line.price - board_day_price,
                                "discount": line.discount or 0,
                            },
                        )
                    )
            else:
                cmds.append(
                    (
                        0,
                        False,
                        {
                            "date": line.date,
                            "price": line.price - board_day_price,
                            "discount": line.discount or 0,
                        },
                    )
                )
        return cmds

    def wrapper_reservation_services(self, info_services, services=False):
        cmds = []
        for info_service in info_services:
            if services:
                service_id = services.filtered(
                    lambda s: s.product_id.id == info_service.productId
                )
                if service_id:
                    service_id = service_id[0]
                    services -= service_id
                else:
                    service_id = False

            cmds.append(
                (
                    0,
                    False,
                    {
                        "product_id": info_service.productId,
                        "product_qty": info_service.quantity,
                        "discount": info_service.discount or 0,
                    },
                )
            )
        return cmds

    def force_api_update_avail(
        self, pms_property_id, room_type_ids, date_from, date_to
    ):
        """
        This method is used to force the update of the availability
        of the given room types in the given dates
        It is used to override potential availability changes on the channel made unilaterally,
        for example, upon entering or canceling a reservation.
        """
        api_clients = (
            self.env["res.users"]
            .sudo()
            .search(
                [
                    ("pms_api_client", "=", True),
                    ("pms_property_ids", "in", pms_property_id),
                ]
            )
        )
        if not room_type_ids or not api_clients:
            return False
        for room_type_id in room_type_ids:
            pms_property = self.env["pms.property"].browse(pms_property_id)
            self.env["pms.property"].sudo().pms_api_push_batch(
                call_type="availability",  # 'availability', 'prices', 'restrictions'
                date_from=date_from.strftime("%Y-%m-%d"),  # 'YYYY-MM-DD'
                date_to=date_to.strftime("%Y-%m-%d"),  # 'YYYY-MM-DD'
                filter_room_type_id=room_type_id,
                pms_property_codes=[pms_property.pms_property_code],
            )
