# Copyright 2021  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsAvailability(models.Model):
    _name = "pms.availability"
    _description = "Room type availability per day"
    _check_pms_properties_auto = True

    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room type for which availability is indicated",
        readonly=True,
        required=True,
        comodel_name="pms.room.type",
        ondelete="cascade",
        check_pms_properties=True,
    )
    date = fields.Date(
        string="Date",
        help="Date for which availability applies",
        readonly=True,
        required=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the availability is directed",
        readonly=True,
        required=True,
        comodel_name="pms.property",
        ondelete="restrict",
        check_pms_properties=True,
    )
    reservation_line_ids = fields.One2many(
        string="Reservation Lines",
        help="They are the lines of the reservation into a reservation,"
        "they corresponds to the nights",
        readonly=True,
        comodel_name="pms.reservation.line",
        inverse_name="avail_id",
        check_pms_properties=True,
    )
    avail_rule_ids = fields.One2many(
        string="Avail record rules",
        comodel_name="pms.availability.plan.rule",
        inverse_name="avail_id",
        check_pms_properties=True,
    )
    real_avail = fields.Integer(
        string="Real Avail",
        help="",
        store=True,
        readonly=True,
        compute="_compute_real_avail",
    )

    _sql_constraints = [
        (
            "room_type_registry_unique",
            "unique(room_type_id, date, pms_property_id)",
            "Only can exists one availability in the same \
                        day for the same room type!",
        )
    ]

    @api.depends(
        "reservation_line_ids",
        "reservation_line_ids.occupies_availability",
        "room_type_id.total_rooms_count",
    )
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
