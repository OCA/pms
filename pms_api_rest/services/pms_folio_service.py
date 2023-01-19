from datetime import datetime, timedelta

from odoo import _, fields
from odoo.exceptions import MissingError, ValidationError
from odoo.osv import expression
from odoo.tools import get_lang

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
                state=dict(folio.fields_get(["state"])["state"]["selection"])[
                    folio.state
                ],
                amountTotal=round(folio.amount_total, 2),
                reservationType=folio.reservation_type,
                pendingAmount=folio.pending_amount,
                lastCheckout=str(folio.last_checkout),
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
        pms_property_id = int(folio_search_param.pmsPropertyId)
        domain_fields.append(("pms_property_id", "=", pms_property_id))

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

        domain_filter = list()
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
            if folio_search_param.filterByState == "byCheckin":
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
            else:
                subdomain_checkin = [
                    [("state", "in", ("confirm", "arrival_delayed"))],
                    [("checkin", "<=", fields.Date.today())],
                ]
                subdomain_checkin = expression.AND(subdomain_checkin)
                subdomain_checkout = [
                    [("state", "in", ("onboard", "departure_delayed"))],
                    [("checkout", "=", fields.Date.today())],
                ]
                subdomain_checkout = expression.AND(subdomain_checkout)
                domain_filter.append(
                    expression.OR([subdomain_checkin, subdomain_checkout])
                )
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
            [("id", "in", reservations_result)], order="write_date desc"
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
                        "preferredRoomId": reservation.preferred_room_id.id
                        if reservation.preferred_room_id
                        else None,
                        "roomTypeId": reservation.room_type_id.id
                        if reservation.room_type_id
                        else None,
                        "adults": reservation.adults,
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
                    }
                )
            result_folios.append(
                PmsFolioShortInfo(
                    id=folio.id,
                    partnerName=folio.partner_name if folio.partner_name else None,
                    partnerPhone=folio.mobile if folio.mobile else None,
                    partnerEmail=folio.email if folio.email else None,
                    amountTotal=round(folio.amount_total, 2),
                    reservations=[] if not reservations else reservations,
                    paymentStateCode=folio.payment_state,
                    paymentStateDescription=dict(
                        folio.fields_get(["payment_state"])["payment_state"][
                            "selection"
                        ]
                    )[folio.payment_state],
                    reservationType=folio.reservation_type,
                    closureReasonId=folio.closure_reason_id,
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
            date=datetime.strptime(pms_account_payment_info.date, "%m/%d/%Y"),
        )

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
            date=datetime.strptime(pms_account_payment_info.date, "%m/%d/%Y"),
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
                            preferredRoomId=reservation.preferred_room_id.id
                            if reservation.preferred_room_id
                            else None,
                            adults=reservation.adults,
                            stateCode=reservation.state,
                            stateDescription=dict(
                                reservation.fields_get(["state"])["state"]["selection"]
                            )[reservation.state],
                            children=reservation.children
                            if reservation.children
                            else None,
                            readyForCheckin=reservation.ready_for_checkin,
                            allowedCheckout=reservation.allowed_checkout,
                            isSplitted=reservation.splitted,
                            priceTotal=round(reservation.price_room_services_set, 2),
                            folioSequence=reservation.folio_sequence
                            if reservation.folio_sequence
                            else None,
                            servicesCount=sum(
                                reservation.service_ids.filtered(
                                    lambda x: not x.is_board_service
                                ).mapped("product_qty")
                            ),
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
    def create_folio(self, pms_folio_info):
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
                "sale_channel_origin_id": pms_folio_info.saleChannelId,
                "agency_id": pms_folio_info.agencyId
                if pms_folio_info.agencyId
                else False,
                "reservation_type": pms_folio_info.reservationType,
                "internal_comment": pms_folio_info.internalComment,
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
                "preconfirm": pms_folio_info.preconfirm,
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
        return folio.id

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
    def update_folio(self, folio_id, pms_folio_info):
        folio = self.env["pms.folio"].browse(folio_id)
        folio_vals = {}
        if not folio:
            raise MissingError(_("Folio not found"))
        if pms_folio_info.cancelReservations:
            folio.action_cancel()
        if pms_folio_info.confirmReservations:
            for reservation in folio.reservation_ids:
                reservation.confirm()
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
        return False
