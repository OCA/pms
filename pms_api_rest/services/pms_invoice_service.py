from datetime import datetime

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.osv import expression

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsInvoiceService(Component):
    _inherit = "base.rest.service"
    _name = "pms.invoice.service"
    _usage = "invoices"
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
        input_param=Datamodel("pms.invoice.search.param"),
        output_param=Datamodel("pms.invoice.info"),
        auth="jwt_api_pms",
    )
    def get_invoices(self, pms_invoice_search_param):
        result_invoices = []

        domain = []
        domain_fields = [
            ("state", "in", ("draft", "posted")),
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("folio_ids", "!=", False),
        ]
        domain_filter = list()

        if pms_invoice_search_param.originAgencyId:
            domain_fields.append(
                ("origin_agency_id", "=", pms_invoice_search_param.originAgencyId),
            )
        if pms_invoice_search_param.pmsPropertyId:
            domain_fields.append(
                ("pms_property_id", "=", pms_invoice_search_param.pmsPropertyId)
            )
        if pms_invoice_search_param.paymentState == "paid":
            domain_fields.append(
                ("payment_state", "in", ("paid", "reversed", "invoicing_legacy"))
            )
        elif pms_invoice_search_param.paymentState == "not_paid":
            domain_fields.append(("payment_state", "in", ("not_paid", "in_payment")))
        elif pms_invoice_search_param.paymentState == "partial":
            domain_fields.append(
                ("payment_state", "=", pms_invoice_search_param.paymentState)
            )
        if pms_invoice_search_param.dateStart and pms_invoice_search_param.dateEnd:
            date_from = fields.Date.from_string(pms_invoice_search_param.dateStart)
            date_to = fields.Date.from_string(pms_invoice_search_param.dateEnd)
            domain_fields.extend(
                [
                    ("invoice_date", ">=", date_from),
                    ("invoice_date", "<=", date_to),
                ]
            )
        if pms_invoice_search_param.filter:
            for search in pms_invoice_search_param.filter.split(" "):
                subdomains = [
                    [("name", "ilike", search)],
                    [("partner_id.display_name", "ilike", search)],
                    [("partner_id.vat", "ilike", search)],
                    [
                        (
                            "partner_id.aeat_identification",
                            "ilike",
                            search,
                        )
                    ],
                    [("folio_ids.name", "ilike", search)],
                ]
                domain_filter.append(expression.OR(subdomains))

        if domain_filter:
            domain = expression.AND([domain_fields, domain_filter[0]])
        else:
            domain = domain_fields
        PmsInvoiceResults = self.env.datamodels["pms.invoice.results"]
        PmsInvoiceInfo = self.env.datamodels["pms.invoice.info"]
        PmsInvoiceLineInfo = self.env.datamodels["pms.invoice.line.info"]
        total_invoices = self.env["account.move"].search_count(domain)
        amount_total = sum(
            self.env["account.move"]
            .search(
                domain,
                order=pms_invoice_search_param.orderBy,
                limit=pms_invoice_search_param.limit,
                offset=pms_invoice_search_param.offset,
            )
            .mapped("amount_total")
        )
        for invoice in self.env["account.move"].search(
            domain,
            order=pms_invoice_search_param.orderBy,
            limit=pms_invoice_search_param.limit,
            offset=pms_invoice_search_param.offset,
        ):

            move_lines = []

            for move_line in invoice.invoice_line_ids:
                move_lines.append(
                    PmsInvoiceLineInfo(
                        id=move_line.id,
                        name=move_line.name if move_line.name else None,
                        quantity=move_line.quantity if move_line.quantity else None,
                        priceUnit=move_line.price_unit
                        if move_line.price_unit
                        else None,
                        total=move_line.price_total if move_line.price_total else None,
                        discount=move_line.discount if move_line.discount else None,
                        displayType=move_line.display_type
                        if move_line.display_type
                        else None,
                        saleLineId=move_line.folio_line_ids[0]
                        if move_line.folio_line_ids
                        else None,
                        isDownPayment=move_line.move_id._is_downpayment(),
                    )
                )
            invoice_date = (
                datetime.combine(invoice.invoice_date, datetime.min.time()).isoformat()
                if invoice.invoice_date
                else datetime.combine(
                    invoice.invoice_date_due, datetime.min.time()
                ).isoformat()
                if invoice.invoice_date_due
                else None
            )
            invoice_url = (
                invoice.get_proforma_portal_url()
                if invoice.state == "draft"
                else invoice.get_portal_url()
            )
            portal_url = (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                + invoice_url
            )
            result_invoices.append(
                PmsInvoiceInfo(
                    id=invoice.id if invoice.id else None,
                    name=invoice.name if invoice.name else None,
                    amount=round(invoice.amount_total, 2)
                    if invoice.amount_total
                    else None,
                    date=invoice_date,
                    state=invoice.state if invoice.state else None,
                    paymentState=invoice.payment_state
                    if invoice.payment_state
                    else None,
                    partnerName=invoice.partner_id.name
                    if invoice.partner_id.name
                    else None,
                    partnerId=invoice.partner_id.id if invoice.partner_id.id else None,
                    moveLines=move_lines if len(move_lines) > 0 else None,
                    folioId=invoice.folio_ids[0] if invoice.folio_ids else None,
                    portalUrl=portal_url,
                    moveType=invoice.move_type,
                    isReversed=invoice.payment_state == "reversed",
                    isDownPaymentInvoice=invoice._is_downpayment(),
                    isSimplifiedInvoice=invoice.journal_id.is_simplified_invoice,
                    originAgencyId=invoice.origin_agency_id.id
                    if invoice.origin_agency_id
                    else None,
                    ref=invoice.ref if invoice.ref else None,
                    pmsPropertyId=invoice.pms_property_id
                    if invoice.pms_property_id
                    else None,
                )
            )
        return PmsInvoiceResults(
            invoices=result_invoices,
            total=round(amount_total, 2),
            totalInvoices=total_invoices,
        )

    @restapi.method(
        [
            (
                [
                    "/p/<int:invoice_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.invoice.info"),
        auth="jwt_api_pms",
    )
    # flake8: noqa: C901
    def update_invoice(self, invoice_id, pms_invoice_info):
        invoice = self.env["account.move"].browse(invoice_id)
        if invoice.move_type in ["in_refund", "out_refund"]:
            raise UserError(_("You can't update a refund invoice"))
        if invoice.payment_state == "reversed":
            raise UserError(_("You can't update a reversed invoice"))
        new_vals = {}
        if (
            pms_invoice_info.partnerId
            and pms_invoice_info.partnerId != invoice.partner_id.id
        ):
            new_vals["partner_id"] = pms_invoice_info.partnerId

        if pms_invoice_info.date:
            invoice_date_info = fields.Date.from_string(pms_invoice_info.date)
            if invoice_date_info != invoice.invoice_date:
                new_vals["invoice_date"] = invoice_date_info

        # If invoice lines are updated, we expect that all lines will be
        # send to service, the lines that are not sent we assume that
        # they have been eliminated
        if pms_invoice_info.moveLines is not None:
            cmd_invoice_lines = self._get_invoice_lines_commands(
                invoice, pms_invoice_info
            )
            if cmd_invoice_lines:
                new_vals["invoice_line_ids"] = cmd_invoice_lines
        new_invoice = False
        if new_vals:
            # Update Invoice
            # When modifying an invoice, depending on the company's configuration,
            # and the invoice state it will be modified directly or a reverse
            # of the current invoice will be created to later create a new one
            # with the updated data.
            # TODO: to create core pms correct_invoice_policy field
            # if invoice.state != "draft" and company.corrective_invoice_policy == "strict":
            if invoice.state == "posted":
                # invoice create refund
                new_invoice = invoice.copy()
                cmd_new_invoice_lines = []
                for item in cmd_invoice_lines:
                    # susbstituted in new_vals reversed invoice line id by new invoice line id
                    if item[0] == 0:
                        cmd_new_invoice_lines.append(item)
                    else:
                        folio_line_ids = self.env["folio.sale.line"].browse(
                            self.env["account.move.line"]
                            .browse(item[1])
                            .folio_line_ids.ids
                        )
                        new_id = new_invoice.invoice_line_ids.filtered(
                            lambda l: l.folio_line_ids == folio_line_ids
                        ).id
                        if item[0] == 2:
                            # delete
                            cmd_new_invoice_lines.append((2, new_id))
                        else:
                            # update
                            cmd_new_invoice_lines.append((1, new_id, item[2]))
                if cmd_new_invoice_lines:
                    new_vals["invoice_line_ids"] = cmd_new_invoice_lines
                invoice._reverse_moves(cancel=True)
                # Update Journal by partner if necessary (simplified invoice -> normal invoice)
                new_vals["journal_id"] = (
                    invoice.pms_property_id._get_folio_default_journal(
                        new_vals.get("partner_id", invoice.partner_id.id)
                    ).id,
                )
                new_invoice.write(new_vals)
                new_invoice.sudo().action_post()
            else:
                new_invoice = self._direct_move_update(invoice, new_vals)
        invoice_to_update = new_invoice or invoice
        # Clean sections without lines
        folio_lines_invoiced = invoice_to_update.invoice_line_ids.folio_line_ids
        for folio_line in folio_lines_invoiced.filtered(
            lambda l: l.display_type == "line_section"
        ):
            if (
                not folio_line.id
                in folio_lines_invoiced.filtered(
                    lambda l: l.display_type != "line_section"
                ).section_id.ids
            ):
                folio_line.invoice_lines.filtered(
                    lambda l: l.move_id == invoice_to_update
                ).unlink()

        if pms_invoice_info.narration is not None:
            invoice_to_update.write({"narration": pms_invoice_info.narration})
        if invoice_to_update.state == "draft" and pms_invoice_info.state == "confirm":
            invoice_to_update.action_post()
        if (
            invoice_to_update.state == "draft"
            and not invoice_to_update.invoice_line_ids
        ):
            invoice_to_update.unlink()
        return invoice_to_update.id or None

    def _direct_move_update(self, invoice, new_vals):
        previus_state = invoice.state
        if previus_state == "posted":
            invoice.button_draft()
        if new_vals:
            updated_invoice_lines_name = False
            # REVIEW: If invoice lines are updated (lines that already existed),
            # the _move_autocomplete_invoice_lines_write called accout.move write
            # method overwrite the move_lines dict and we lost the new name values,
            # so, we need to save and rewrite it. (core odoo methods)

            # 1- save send invoice line name values:
            if new_vals.get("invoice_line_ids"):
                updated_invoice_lines_name = {
                    line[1]: line[2]["name"]
                    for line in new_vals["invoice_line_ids"]
                    if line[0] == 1 and "name" in line[2]
                }
            # _move_autocomplete_invoice_lines_write overwrite invoice line name values
            # so, we need to save and rewrite it. in all line that are not updated or deleted
            for line in invoice.invoice_line_ids.filtered(
                lambda l: l.id not in updated_invoice_lines_name
                if updated_invoice_lines_name
                else []
                and l.id
                not in [
                    line[1] for line in new_vals["invoice_line_ids"] if line[0] == 2
                ]
            ):
                updated_invoice_lines_name[line.id] = line.name
            # 2- update invoice
            invoice.write(new_vals)
            # 3- rewrite invoice line name values:
            if updated_invoice_lines_name:
                for item in updated_invoice_lines_name:
                    invoice.invoice_line_ids.filtered(lambda l: l.id == item).write(
                        {"name": updated_invoice_lines_name[item]}
                    )
            # 4- Avoid set number invoice in draft invoices
            if previus_state == "draft":
                invoice.write({"name": "/"})
        if previus_state == "posted":
            invoice.action_post()
        return invoice

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.invoice.info"),
        auth="jwt_api_pms",
    )
    def create_invoice(self, pms_invoice_info):
        if pms_invoice_info.originDownPaymentId:
            if not pms_invoice_info.partnerId:
                raise UserError(_("For manual invoice, partner is required"))
            payment = self.env["account.payment"].browse(
                pms_invoice_info.originDownPaymentId
            )
            self.env["account.payment"]._create_downpayment_invoice(
                payment=payment,
                partner_id=pms_invoice_info.partnerId,
            )

    @restapi.method(
        [
            (
                [
                    "/<int:invoice_id>/mail",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.mail.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_invoice_mail(self, invoice_id):
        invoice = self.env["account.move"].browse(invoice_id)
        compose_vals = {
            "template_id": self.env.ref("account.email_template_edi_invoice").id,
            "model": "account.move",
            "res_ids": invoice.id,
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
                    "/<int:invoice_id>/send-mail",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.mail.info"),
        auth="jwt_api_pms",
    )
    def send_invoice_mail(self, invoice_id, pms_mail_info):
        invoice = self.env["account.move"].browse(invoice_id)
        recipients = pms_mail_info.emailAddresses
        template = self.env.ref(
            "account.email_template_edi_invoice", raise_if_not_found=False
        )
        email_values = {
            "email_to": ",".join(recipients) if recipients else False,
            "email_from": invoice.pms_property_id.email
            if invoice.pms_property_id.email
            else False,
            "subject": pms_mail_info.subject,
            "body_html": pms_mail_info.bodyMail,
            "partner_ids": pms_mail_info.partnerIds
            if pms_mail_info.partnerIds
            else False,
            "recipient_ids": pms_mail_info.partnerIds
            if pms_mail_info.partnerIds
            else False,
            "auto_delete": False,
        }
        template.send_mail(invoice.id, force_send=True, email_values=email_values)
        return True

    def _get_invoice_lines_commands(self, invoice, pms_invoice_info):
        cmd_invoice_lines = []
        for line in invoice.invoice_line_ids:
            line_info = [
                item for item in pms_invoice_info.moveLines if item.id == line.id
            ]
            if line_info:
                line_info = line_info[0]
                line_values = {}
                if line_info.name:
                    line_values["name"] = line_info.name
                if line_info.quantity and line_info.quantity != line.quantity:
                    line_values["quantity"] = line_info.quantity
                if line_values:
                    cmd_invoice_lines.append((1, line.id, line_values))
            elif not line.display_type:
                cmd_invoice_lines.append((2, line.id))
        # Get the new lines to add in invoice
        newInvoiceLinesInfo = list(
            filter(lambda item: not item.id, pms_invoice_info.moveLines)
        )
        if newInvoiceLinesInfo:
            partner = (
                self.env["res.partner"].browse(pms_invoice_info.partnerId)
                if pms_invoice_info.partnerId
                else invoice.partner_id
            )
            folios = self.env["pms.folio"].browse(
                list(
                    {
                        self.env["folio.sale.line"].browse(line.saleLineId).folio_id.id
                        for line in list(
                            filter(
                                lambda item: item.name,
                                pms_invoice_info.moveLines,
                            )
                        )
                    }
                )
            )
            lines_to_invoice = {
                newInvoiceLinesInfo[i].saleLineId: newInvoiceLinesInfo[i].quantity
                for i in range(0, len(newInvoiceLinesInfo))
            }
            # Add sections to invoice lines
            new_section_ids = (
                self.env["folio.sale.line"]
                .browse([line.saleLineId for line in newInvoiceLinesInfo])
                .filtered(
                    lambda l: l.section_id.id
                    not in invoice.invoice_line_ids.mapped("folio_line_ids.id")
                )
                .mapped("section_id.id")
            )
            if new_section_ids:
                lines_to_invoice.update(
                    {section_id: 0 for section_id in new_section_ids}
                )
            new_invoice_lines = [
                item["invoice_line_ids"]
                for item in folios.get_invoice_vals_list(
                    lines_to_invoice=lines_to_invoice,
                    partner_invoice_id=partner.id,
                )
            ][0]
            # Update name of new invoice lines
            for item in filter(lambda l: not l[2]["display_type"], new_invoice_lines):
                item[2]["name"] = [
                    line.name
                    for line in newInvoiceLinesInfo
                    if [line.saleLineId] == item[2]["folio_line_ids"][0][2]
                ][0]
            cmd_invoice_lines.extend(new_invoice_lines)
        return cmd_invoice_lines
