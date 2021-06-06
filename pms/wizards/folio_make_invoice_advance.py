# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FolioAdvancePaymentInv(models.TransientModel):
    _name = "folio.advance.payment.inv"
    _description = "Folio Advance Payment Invoice"

    partner_invoice_id = fields.Many2one(
        string="Billing contact",
        help="Invoice address for current partner",
        default=lambda self: self._default_partner_invoice_id(),
        comodel_name="res.partner",
    )
    advance_payment_method = fields.Selection(
        string="Create Invoice",
        help="A standard invoice is issued with all the order \
                lines ready for invoicing, \
                according to their invoicing policy \
                (based on ordered or delivered quantity).",
        required=True,
        default="delivered",
        selection=[
            ("delivered", "Regular invoice"),
            ("percentage", "Down payment (percentage)"),
            ("fixed", "Down payment (fixed amount)"),
        ],
    )
    bill_services = fields.Boolean(
        string="Bill Services", help="Bill Services", default=True
    )
    bill_rooms = fields.Boolean(string="Bill Rooms", help="Bill Rooms", default=True)
    deduct_down_payments = fields.Boolean(
        string="Deduct down payments", help="Deduct down payments", default=True
    )
    has_down_payments = fields.Boolean(
        string="Has down payments",
        help="Has down payments",
        readonly=True,
        default=lambda self: self._default_has_down_payment(),
    )
    product_id = fields.Many2one(
        string="Down Payment Product",
        default=lambda self: self._default_product_id(),
        comodel_name="product.product",
        domain=[("type", "=", "service")],
    )
    count = fields.Integer(
        string="Order Count",
        default=lambda self: self._count(),
    )
    amount = fields.Float(
        string="Down Payment Amount",
        help="The percentage of amount to be invoiced in advance, taxes excluded.",
        digits="Account",
    )
    currency_id = fields.Many2one(
        string="Currency",
        help="Currency used in invoices",
        comodel_name="res.currency",
        default=lambda self: self._default_currency_id(),
    )
    fixed_amount = fields.Monetary(
        string="Down Payment Amount (Fixed)",
        help="The fixed amount to be invoiced in advance, taxes excluded.",
    )
    deposit_account_id = fields.Many2one(
        string="Income Account",
        help="Account used for deposits",
        default=lambda self: self._default_deposit_account_id(),
        comodel_name="account.account",
        domain=[("deprecated", "=", False)],
    )
    deposit_taxes_id = fields.Many2many(
        string="Customer Taxes",
        help="Taxes used for deposits",
        default=lambda self: self._default_deposit_taxes_id(),
        comodel_name="account.tax",
    )

    @api.model
    def _count(self):
        return len(self._context.get("active_ids", []))

    @api.model
    def _default_product_id(self):
        product_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale.default_deposit_product_id")
        )
        return self.env["product.product"].browse(int(product_id)).exists()

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id()._get_product_accounts()["income"]

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().taxes_id

    @api.model
    def _default_has_down_payment(self):
        if self._context.get("active_model") == "pms.folio" and self._context.get(
            "active_id", False
        ):
            folio = self.env["pms.folio"].browse(self._context.get("active_id"))
            return folio.sale_line_ids.filtered(lambda line: line.is_downpayment)

        return False

    @api.model
    def _default_currency_id(self):
        if self._context.get("active_model") == "pms.folio" and self._context.get(
            "active_id", False
        ):
            sale_order = self.env["pms.folio"].browse(self._context.get("active_id"))
            return sale_order.currency_id

    @api.model
    def _default_partner_invoice_id(self):
        if self._context.get("active_model") == "pms.folio" and self._context.get(
            "active_id", False
        ):
            folio = self.env["pms.folio"].browse(self._context.get("active_id", []))
            return folio.partner_invoice_ids[0]

    def _get_advance_details(self, order):
        context = {"lang": order.partner_id.lang}
        if self.advance_payment_method == "percentage":
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount)
        else:
            amount = self.fixed_amount
            name = _("Down Payment")
        del context

        return amount, name

    @api.onchange("advance_payment_method")
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == "percentage":
            amount = self.default_get(["amount"]).get("amount")
            return {"value": {"amount": amount}}
        return {}

    def _prepare_invoice_values(self, order, name, amount, line):
        invoice_vals = {
            "ref": order.client_order_ref,
            "move_type": "out_invoice",
            "invoice_origin": order.name,
            "invoice_user_id": order.user_id.id,
            "narration": order.note,
            "partner_id": self.partner_invoice_id
            if self.partner_invoice_id
            else order.partner_invoice_id.id,
            "currency_id": order.pricelist_id.currency_id.id,
            "payment_reference": order.reference,
            "invoice_payment_term_id": order.payment_term_id.id,
            "partner_bank_id": order.company_id.partner_id.bank_ids[:1].id,
            # 'campaign_id': order.campaign_id.id,
            # 'medium_id': order.medium_id.id,
            # 'source_id': order.source_id.id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": name,
                        "price_unit": amount,
                        "quantity": 1.0,
                        "product_id": self.product_id.id,
                        "product_uom_id": line.product_uom.id,
                        "tax_ids": [(6, 0, line.tax_ids.ids)],
                        "folio_line_ids": [(6, 0, [line.id])],
                        "analytic_tag_ids": [(6, 0, line.analytic_tag_ids.ids)],
                        "analytic_account_id": order.analytic_account_id.id or False,
                    },
                )
            ],
        }

        return invoice_vals

    def _create_invoice(self, order, line, amount):
        if (self.advance_payment_method == "percentage" and self.amount <= 0.00) or (
            self.advance_payment_method == "fixed" and self.fixed_amount <= 0.00
        ):
            raise UserError(_("The value of the down payment amount must be positive."))

        amount, name = self._get_advance_details(order)

        invoice_vals = self._prepare_invoice_values(order, name, amount, line)

        if order.fiscal_position_id:
            invoice_vals["fiscal_position_id"] = order.fiscal_position_id.id
        invoice = (
            self.env["account.move"].sudo().create(invoice_vals).with_user(self.env.uid)
        )
        invoice.message_post_with_view(
            "mail.message_origin_link",
            values={"self": invoice, "origin": order},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        return invoice

    def _prepare_line(self, order, analytic_tag_ids, tax_ids, amount):
        context = {"lang": order.partner_id.lang}
        so_values = {
            "name": _("Down Payment: %s") % (time.strftime("%m %Y"),),
            "price_unit": amount,
            "product_uom_qty": 0.0,
            "folio_id": order.id,
            "discount": 0.0,
            "product_uom": self.product_id.uom_id.id,
            "product_id": self.product_id.id,
            "analytic_tag_ids": analytic_tag_ids,
            "tax_ids": [(6, 0, tax_ids)],
            "is_downpayment": True,
            "sequence": order.sale_line_ids
            and order.sale_line_ids[-1].sequence + 1
            or 10,
        }
        del context
        return so_values

    def create_invoices(self):
        folios = self.env["pms.folio"].browse(self._context.get("active_ids", []))

        if self.advance_payment_method == "delivered":
            lines_to_invoice = self._get_lines_to_invoice(
                folios=folios,
                bill_services=self.bill_services,
                bill_rooms=self.bill_rooms,
            )
            folios._create_invoices(
                final=self.deduct_down_payments,
                lines_to_invoice=lines_to_invoice,
                partner_invoice_id=self.partner_invoice_id
                if self.partner_invoice_id
                else False,
            )
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env["product.product"].create(vals)
                self.env["ir.config_parameter"].sudo().set_param(
                    "sale.default_deposit_product_id", self.product_id.id
                )

            sale_line_obj = self.env["folio.sale.line"]
            for order in folios:
                amount, name = self._get_advance_details(order)

                if self.product_id.invoice_policy != "order":
                    raise UserError(
                        _(
                            """The product used to invoice a down payment should
                            have an invoice policy set to "Ordered quantities".
                            Please update your deposit product to be able
                            to create a deposit invoice."""
                        )
                    )
                if self.product_id.type != "service":
                    raise UserError(
                        _(
                            """The product used to invoice a down payment should
                            be of type 'Service'.
                            Please use another product or update this product."""
                        )
                    )
                taxes = self.product_id.taxes_id.filtered(
                    lambda r: not order.company_id or r.company_id == order.company_id
                )
                tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id).ids
                analytic_tag_ids = []
                for line in order.sale_line_ids:
                    analytic_tag_ids = [
                        (4, analytic_tag.id, None)
                        for analytic_tag in line.analytic_tag_ids
                    ]

                line_values = self._prepare_line(
                    order, analytic_tag_ids, tax_ids, amount
                )
                line = sale_line_obj.sudo().create(line_values)
                self._create_invoice(order, line, amount)
        if self._context.get("open_invoices", False):
            return folios.action_view_invoice()
        return {"type": "ir.actions.act_window_close"}

    def _prepare_deposit_product(self):
        return {
            "name": "Down payment",
            "type": "service",
            "invoice_policy": "order",
            "property_account_income_id": self.deposit_account_id.id,
            "taxes_id": [(6, 0, self.deposit_taxes_id.ids)],
            "company_id": False,
        }

    @api.model
    def _get_lines_to_invoice(self, folios, bill_services=True, bill_rooms=True):
        lines_to_invoice = folios.sale_line_ids
        if not bill_services:
            lines_to_invoice = lines_to_invoice - lines_to_invoice.filtered(
                lambda l: l.service_id and not l.service_id.is_board_service
            )
        if not bill_rooms:
            lines_to_invoice = lines_to_invoice.filtered(
                lambda l: l.reservation_id and l.reservation_line_ids
            )
        if not lines_to_invoice:
            raise UserError(_("Nothing to invoice"))

        lines_dict = dict()
        for line in lines_to_invoice:
            if not line.display_type:
                lines_dict[line.id] = line.qty_to_invoice
            else:
                lines_dict[line.id] = 0
        return lines_dict
        # return lines_to_invoice
