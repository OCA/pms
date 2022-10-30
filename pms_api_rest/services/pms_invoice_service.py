from datetime import datetime

from odoo import _, fields

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsInvoiceService(Component):
    _inherit = "base.rest.service"
    _name = "pms.room.service"
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
        company = invoice.company_id

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
            new_vals["reservation_line_ids"] = []
            for line in invoice.invoice_line_ids:
                line_info = [
                    item.id for item in pms_invoice_info.moveLines if item.id == line.id
                ]
                if line_info:
                    line_values = {}
                    if line_info.name and line_info.name != line.name:
                        line_values["name"] = line_info.name
                    if line_info.quantity and line_info.quantity != line.quantity:
                        line_values["quantity"] = line_info.quantity
                    new_vals["reservation_line_ids"].append((1, 4, line_values))
                else:
                    new_vals["reservation_line_ids"].append((2, line.id))

        if not new_vals:
            return invoice.id

        # Update Invoice
        # When modifying an invoice, depending on the company's configuration,
        # and the invoice stateit will be modified directly or a reverse
        # of the current invoice will be created to later create a new one
        # with the updated data.
        if invoice.state != "draft" and company.corrective_invoice_policy == "strict":
            # invoice create refund
            # new invoice with new_vals
            move_reversal = (
                self.env["account.move.reversal"]
                .with_context(active_model="account.move", active_ids=invoice.ids)
                .create(
                    {
                        "date": fields.Date.today() + datetime.timedelta(days=7),
                        "reason": _("Invoice modification"),
                        "refund_method": "modify",
                    }
                )
            )
            reversal_action = move_reversal.reverse_moves()
            reverse_invoice = self.env["account.move"].browse(reversal_action["res_id"])
            invoice = reverse_invoice

        invoice = self._direct_move_update(invoice, new_vals)
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
