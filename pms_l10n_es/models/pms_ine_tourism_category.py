from odoo import fields, models


class PmsIneTourismCategory(models.Model):
    _name = "pms.ine.tourism.category"
    _description = "Hotel category in the Ministry of Tourism. Used for INE statistics."

    name = fields.Char("Category", required=True)
    category_type = fields.Char("Category type", required=True)

    def name_get(self):
        data = []
        for record in self:
            display_value = record.category_type + " (" + record.name + ") "
            data.append((record.id, display_value))
        return data
