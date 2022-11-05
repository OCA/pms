from odoo import _, fields

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
                    "/p/<int:invoice_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.invoice.info"),
        auth="jwt_api_pms",
    )
    def update_invoice(self, invoice_id, pms_invoice_info):
        invoice = self.env["account.move"].browse(invoice_id)

        # Build update values dict
        # TODO: Missing data:
        # - invoice comment (narration)
        # - add new invoice lines (from saleLines selected?)

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
        if pms_invoice_info.moveLines and pms_invoice_info.moveLines is not None:
            new_vals["invoice_line_ids"] = []
            for line in invoice.invoice_line_ids:
                line_info = [
                    item for item in pms_invoice_info.moveLines if item.id == line.id
                ]
                if line_info:
                    line_info = line_info[0]
                    line_values = {}
                    if line_info.name and line_info.name != line.name:
                        line_values["name"] = line_info.name
                    if line_info.quantity and line_info.quantity != line.quantity:
                        line_values["quantity"] = line_info.quantity
                    if line_values:
                        new_vals["invoice_line_ids"].append((1, line.id, line_values))
                else:
                    new_vals["invoice_line_ids"].append((2, line.id))
            # Get the new lines to add in invoice
            new_invoice_lines_info = list(
                filter(lambda item: not item.id, pms_invoice_info.moveLines)
            )
            if new_invoice_lines_info:
                partner = (
                    self.env["res.partner"].browse(pms_invoice_info.partnerId)
                    if pms_invoice_info.partnerId
                    else invoice.partner_id
                )
                folios = self.env["pms.folio"].browse(
                    list(
                        {
                            self.env["folio.sale.line"]
                            .browse(line.saleLineId)
                            .folio_id.id
                            for line in list(
                                filter(
                                    lambda item: item.name,
                                    pms_invoice_info.moveLines,
                                )
                            )
                        }
                    )
                )
                new_vals["invoice_line_ids"].extend(
                    [
                        item["invoice_line_ids"]
                        for item in folios.get_invoice_vals_list(
                            lines_to_invoice={
                                new_invoice_lines_info[i]
                                .saleLineId: new_invoice_lines_info[i]
                                .quantity
                                for i in range(0, len(new_invoice_lines_info))
                            },
                            partner_invoice_id=partner.id,
                        )
                    ][0]
                )
        if not new_vals:
            return invoice.id

        # Update Invoice
        # When modifying an invoice, depending on the company's configuration,
        # and the invoice stateit will be modified directly or a reverse
        # of the current invoice will be created to later create a new one
        # with the updated data.
        # TODO: to create core pms correct_invoice_policy field
        # if invoice.state != "draft" and company.corrective_invoice_policy == "strict":
        if invoice.state != "draft":
            # invoice create refund
            # new invoice with new_vals
            move_reversal = (
                self.env["account.move.reversal"]
                .with_context(active_model="account.move", active_ids=invoice.ids)
                .create(
                    {
                        "date": fields.Date.today(),
                        "reason": _("Invoice modification"),
                        "refund_method": "modify",
                    }
                )
            )
            reversal_action = move_reversal.reverse_moves()
            reverse_invoice = self.env["account.move"].browse(reversal_action["res_id"])
            invoice = reverse_invoice

        invoice = self._direct_move_update(invoice, new_vals)
        # Update invoice lines name
        for item in pms_invoice_info.moveLines:
            if item.saleLineId in invoice.invoice_line_ids.mapped("folio_line_ids.id"):
                invoice_line = invoice.invoice_line_ids.filtered(
                    lambda r: item.saleLineId in r.folio_line_ids.ids
                )
                invoice_line.write({"name": item.name})
        return invoice.id

    def _direct_move_update(self, invoice, new_vals):
        previus_state = invoice.state
        if previus_state == "posted":
            invoice.button_draft()
        if new_vals:
            invoice.write(new_vals)
        if previus_state == "posted":
            invoice.action_post()
        return invoice

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
