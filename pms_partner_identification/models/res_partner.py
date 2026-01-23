from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    identification_number = fields.Char(search="_search_identification_number")

    def _search_identification_number(self, operator, value):
        id_numbers = self.env["res.partner.id_number"].search(
            [("name", operator, value)]
        )
        return [("id_numbers.id", "in", id_numbers.ids)]
