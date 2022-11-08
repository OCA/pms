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
                amountTotal=round(folio.amount_total, 2),
                reservationType=folio.reservation_type,
                pendingAmount=folio.pending_amount,
                lastCheckout=str(folio.last_checkout),
                internalComment=folio.internal_comment
                if folio.internal_comment
                else None,
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
                        "splitted": reservation.splitted,
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
                for payment in folio.payment_ids:
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
        journal_id = self.env["account.journal"].browse(
            pms_account_payment_info.journalId
        )
        reservations = (
            self.env["pms.reservation"].browse(pms_account_payment_info.reservationIds)
            if pms_account_payment_info.reservationIds
            else False
        )
        self.env["pms.folio"].do_payment(
            journal_id,
            journal_id.suspense_account_id,
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
        journal_id = self.env["account.journal"].browse(
            pms_account_payment_info.journalId
        )
        self.env["pms.folio"].do_refund(
            journal_id,
            journal_id.suspense_account_id,
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
                for reservation in folio.reservation_ids:
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
                            splitted=reservation.splitted,
                            priceTotal=round(reservation.price_room_services_set, 2),
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

        return folio.id

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
                            qtyToInvoice=sale_line.qty_to_invoice
                            if sale_line.qty_to_invoice
                            else None,
                            qtyInvoiced=sale_line.qty_invoiced
                            if sale_line.qty_invoiced
                            else None,
                            priceTotal=sale_line.price_total
                            if sale_line.price_total
                            else None,
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
                                displayType=move_line.display_type
                                if move_line.display_type
                                else None,
                                saleLineId=move_line.folio_line_ids
                                if move_line.folio_line_ids
                                else None,
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
                    invoices.append(
                        PmsFolioInvoiceInfo(
                            id=move.id if move.id else None,
                            name=move.name if move.name else None,
                            amount=round(move.amount_total, 2)
                            if move.amount_total
                            else None,
                            date=move.invoice_date.strftime("%d/%m/%Y")
                            if move.invoice_date
                            else None,
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
        for item in invoice_info.saleLines:
            if item.qtyToInvoice:
                lines_to_invoice_dict[item.id] = item.qtyToInvoice

        sale_lines_to_invoice = self.env["folio.sale.line"].browse(
            lines_to_invoice_dict.keys()
        )
        folios_to_invoice = sale_lines_to_invoice.folio_id
        invoices = folios_to_invoice._create_invoices(
            lines_to_invoice=lines_to_invoice_dict,
            partner_invoice_id=invoice_info.partnerId,
        )
        for item in invoice_info.saleLines:
            if item.id in invoices.invoice_line_ids.mapped("folio_line_ids.id"):
                invoice_line = invoices.invoice_line_ids.filtered(
                    lambda r: item.id in r.folio_line_ids.ids
                )
                invoice_line.write({"name": item.name})
        if invoice_info.narration:
            invoices.write({"narration": invoice_info.narration})

        return invoices.ids
