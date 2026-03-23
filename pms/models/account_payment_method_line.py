from odoo import fields, models


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    allowed_on_pms = fields.Boolean(
        "Allowed on PMS",
        help="Use to pay for reservations",
    )
