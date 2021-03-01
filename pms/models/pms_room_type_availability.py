# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoomTypeAvailability(models.Model):
    _name = "pms.room.type.availability"
    _description = "Room type availability per day"

    room_type_id = fields.Many2one(
        comodel_name="pms.room.type",
        string="Room Type",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
    )
    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        ondelete="restrict",
        required=True,
        readonly=True,
    )
    reservation_line_ids = fields.One2many(
        string="Reservation Lines",
        comodel_name="pms.reservation.line",
        inverse_name="avail_id",
        readonly=True,
    )
    real_avail = fields.Integer(
        compute="_compute_real_avail",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "room_type_registry_unique",
            "unique(room_type_id, date, pms_property_id)",
            "Only can exists one availability in the same \
                        day for the same room type!",
        )
    ]

    @api.depends("reservation_line_ids.occupies_availability")
    def _compute_real_avail(self):
        for record in self:
            Rooms = self.env["pms.room"]
            RoomLines = self.env["pms.reservation.line"]
            total_rooms = Rooms.search_count(
                [
                    ("room_type_id", "=", record.room_type_id.id),
                    ("pms_property_id", "=", record.pms_property_id.id),
                ]
            )
            room_ids = record.room_type_id.mapped("room_ids.id")
            rooms_not_avail = RoomLines.search_count(
                [
                    ("date", "=", record.date),
                    ("room_id", "in", room_ids),
                    ("pms_property_id", "=", record.pms_property_id.id),
                    ("occupies_availability", "=", True),
                    # ("id", "not in", current_lines if current_lines else []),
                ]
            )
            record.real_avail = total_rooms - rooms_not_avail

    @api.constrains(
        "room_type_id",
        "pms_property_id",
    )
    def _check_property_integrity(self):
        for rec in self:
            if rec.pms_property_id and rec.room_type_id:
                if (
                    rec.room_type_id.pms_property_ids.ids
                    and rec.pms_property_id.id
                    not in rec.room_type_id.pms_property_ids.ids
                ):
                    raise ValidationError(
                        _("Property not allowed on availability day compute")
                    )
