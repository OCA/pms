# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    pms_property_id = fields.Many2one("pms.property", string="Property")

    @api.model
    def _next_sequence_property(self, pms_property_id, code):
        sequence = self.search(
            [
                ("code", "=", code),
                ("pms_property_id", "=", pms_property_id),
            ]
        )
        if not sequence:
            sequence = self.search(
                [
                    ("code", "=", code),
                    ("pms_property_id", "=", False),
                ]
            )
        return sequence._next_do() or _("New")
