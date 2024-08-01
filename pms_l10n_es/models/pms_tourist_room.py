# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsProperty(models.Model):
    _inherit = "pms.property"

    total_tourist_rooms = fields.Integer(
        string="Tourist Rooms",
        help="Number of tourist rooms in the hotel.",
        compute="_compute_total_rooms",
        store=True,
        default=lambda self: self._get_default_total_rooms(),
    )

    @api.depends("room_ids")
    def _compute_total_rooms(self):
        for record in self:
            record.total_tourist_rooms = len(record.room_ids)

    @api.constrains("total_tourist_rooms")
    def _check_total_tourism_rooms(self):
        for record in self:
            if record.total_tourist_rooms > len(record.room_ids):
                raise ValidationError(
                    _(
                        "The number of tourist rooms cannot exceed the total number of rooms."
                    )
                )

    @api.model
    def _get_default_total_rooms(self):
        return len(self.room_ids)
