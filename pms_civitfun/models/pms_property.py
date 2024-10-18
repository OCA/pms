from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    use_civitfun = fields.Boolean(
        string="Use Civitfun",
        help="Use Civitfun",
    )
    civitfun_property_code = fields.Char(
        string="Civitfun Property Code",
        help="Civitfun Property Code",
    )
    civitfun_payment_journal_id = fields.Many2one(
        string="Civitfun Journal Payments",
        help="Journal to civitfun payments",
        comodel_name="account.journal",
        ondelete="restrict",
    )
