from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    institution = fields.Selection(
        [
            ("guardia_civil", "Guardia Civil"),
            ("policia_nacional", "Policía Nacional (soon)"),
            ("ertxaintxa", "Ertxaintxa (soon)"),
            ("mossos", "Mossos_d'esquadra (soon)"),
        ],
        string="Institution",
        default="guardia_civil",
        help="Institution to send daily guest data.",
    )
    institution_property_id = fields.Char(
        string="Institution property id",
        size=10,
        help="Id provided by institution to send data from property.",
    )
    institution_user = fields.Char(
        string="Institution user", help="User provided by institution to send the data."
    )
    institution_password = fields.Char(
        string="Institution password",
        help="Password provided by institution to send the data.",
    )
