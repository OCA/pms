from odoo import fields, models


class PmsIneTourismCategory(models.Model):
    _name = "pms.ine.tourism.type.category"
    _description = "Hotel category in the Ministry of Tourism. Used for INE statistics."

    type = fields.Char(required=True)
    category = fields.Char(required=True)

    def name_get(self):
        data = []
        for record in self:
            display_value = record.category + " (" + record.type + ") "
            data.append((record.id, display_value))
        return data
