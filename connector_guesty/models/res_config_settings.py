# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    guesty_backend_id = fields.Many2one(
        "backend.guesty", string="Guesty backend connector"
    )

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env.company.guesty_backend_id = self.guesty_backend_id.id
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(guesty_backend_id=self.env.company.guesty_backend_id)
        return res
