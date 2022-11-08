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
    )
    internal_transfer_id = fields.Many2one(
        "account.payment",
        string="Internal Transfer Relation",
        help="Internal transfer relation",
    )

    @api.depends("payment_type", "partner_type")
    def _compute_pms_api_transaction_type(self):
        for record in self:
            if record.is_internal_transfer:
                record.pms_api_transaction_type = "internal_transfer"
            elif record.partner_type == "customer":
                if record.payment_type == "inbound":
                    record.pms_api_transaction_type = "customer_inbound"
                else:
                    record.pms_api_transaction_type = "customer_outbound"
            elif record.partner_type == "supplier":
                if record.payment_type == "outbound":
                    record.pms_api_transaction_type = "supplier_outbound"
                else:
                    record.pms_api_transaction_type = "supplier_inbound"
            else:
                record.pms_api_transaction_type = False
