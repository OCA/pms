from odoo import fields, models


class PmsRoom(models.Model):
    _inherit = "pms.room"

    in_ine = fields.Boolean(
        help="Take it into account to generate INE statistics",
        default=True,
    )
    institution_independent_account = fields.Boolean(
        string="Independent account for institution (travel reports)",
        help="This room has an independent account",
        default=False,
    )
    institution = fields.Selection(
        [
            ("ses", "SES"),
            ("ertxaintxa", "Ertxaintxa (soon)"),
            ("mossos", "Mossos_d'esquadra (soon)"),
        ],
        help="Institution to send daily guest data.",
        required=False,
    )
    institution_property_id = fields.Char(
        help="Id provided by institution to send data from property.",
    )
    ses_url = fields.Char(
        help="URL to send the data to SES",
    )
    institution_user = fields.Char(
        help="User provided by institution to send the data."
    )
    institution_password = fields.Char(
        help="Password provided by institution to send the data.",
    )
    institution_lessor_id = fields.Char(
        help="Id provided by institution to send data from lessor.",
    )
