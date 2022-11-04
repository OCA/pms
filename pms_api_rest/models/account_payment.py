from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    pms_api_transaction_type = fields.Selection(
        selection=[
            ("customer_inbound", "Customer Payment"),
            ("customer_outbound", "Customer Refund"),
            ("supplier_outbound", "Supplier Payment"),
            ("supplier_inbound", "Supplier Refund"),
            ("internal_transfer", "Internal Transfer"),
        ],
        string="PMS API Transaction Type",
        help="Transaction type for PMS API",
        compute="_compute_pms_api_transaction_type",
        store=True,
    )

    @api.depends("payment_type", "partner_type")
    def _compute_pms_api_transaction_type(self):
        for record in self:
            if record.is_internal_transfer:
                return "internal_transfer"
            if record.partner_type == "customer":
                if record.payment_type == "inbound":
                    return "customer_payment"
                else:
                    return "customer_refund"
            if record.partner_type == "supplier":
                if record.payment_type == "inbound":
                    return "supplier_payment"
                else:
                    return "supplier_refund"
            return False
