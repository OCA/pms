from odoo import _, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    police_type = fields.Selection(
                                    [
                                        ("guardia_civil", "Guardia Civil"),
                                        ("policia_nacional","Policía Nacional"),
                                        ("ertxaintxa", "Ertxaintxa"),
                                        ("mossos", "Mossos_d'esquadra")
                                    ],
                                    string="Police Type",
                                    default="guardia_civil")
    police_number = fields.Char("Police Number", size=10)
    police_user = fields.Char("Police User")
    police_pass = fields.Char("Police Password")
