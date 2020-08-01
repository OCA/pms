# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoomTypeRestrictionItem(models.Model):
    _name = "pms.room.type.restriction.item"
    _description = "Reservation restriction by day"

    # Field Declarations
    restriction_id = fields.Many2one(
        "pms.room.type.restriction", "Restriction Plan", ondelete="cascade", index=True
    )
    room_type_id = fields.Many2one(
        "pms.room.type", "Room Type", required=True, ondelete="cascade"
    )
    date = fields.Date("Date")

    min_stay = fields.Integer("Min. Stay")
    min_stay_arrival = fields.Integer("Min. Stay Arrival")
    max_stay = fields.Integer("Max. Stay")
    max_stay_arrival = fields.Integer("Max. Stay Arrival")
    closed = fields.Boolean("Closed")
    closed_departure = fields.Boolean("Closed Departure")
    closed_arrival = fields.Boolean("Closed Arrival")

    _sql_constraints = [
        (
            "room_type_registry_unique",
            "unique(restriction_id, room_type_id, date)",
            "Only can exists one restriction in the same \
                         day for the same room type!",
        )
    ]

    # Constraints and onchanges

    @api.constrains("min_stay", "min_stay_arrival", "max_stay", "max_stay_arrival")
    def _check_min_stay(self):
        for record in self:
            if record.min_stay < 0:
                raise ValidationError(_("Min. Stay can't be less than zero"))
            elif record.min_stay_arrival < 0:
                raise ValidationError(_("Min. Stay Arrival can't be less than zero"))
            elif record.max_stay < 0:
                raise ValidationError(_("Max. Stay can't be less than zero"))
            elif record.max_stay_arrival < 0:
                raise ValidationError(_("Max. Stay Arrival can't be less than zero"))
