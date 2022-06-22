# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    guesty_ids = fields.One2many("res.partner.guesty", "partner_id")

    def split_name(self):
        name_values = self.name.split(" ")
        if len(name_values) == 0:
            raise ValidationError(_("No name defined"))

        if len(name_values) == 1:
            return name_values[0], None

        if len(name_values) == 2:
            return name_values[0], name_values[1]

        if len(name_values) >= 3:
            return name_values[0], " ".join(name_values[1:-1])
