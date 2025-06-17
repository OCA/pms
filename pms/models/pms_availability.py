# Copyright 2021  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

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
        index=True,
        comodel_name="pms.room.type",
        ondelete="cascade",
        check_pms_properties=True,
    )
    date = fields.Date(
        help="Date for which availability applies",
        readonly=True,
        required=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the availability is directed",
        readonly=True,
        required=True,
        index=True,
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
        store=True,
        readonly=True,
        compute="_compute_real_avail",
    )
    parent_avail_id = fields.Many2one(
        string="Parent Avail",
        help="Parent availability for this availability",
        comodel_name="pms.availability",
        ondelete="restrict",
        compute="_compute_parent_avail_id",
        store=True,
        index=True,
        check_pms_properties=True,
    )
    child_avail_ids = fields.One2many(
        string="Child Avails",
        help="Child availabilities for this availability",
        comodel_name="pms.availability",
        inverse_name="parent_avail_id",
        compute="_compute_child_avail_ids",
        store=True,
        check_pms_properties=True,
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
        "parent_avail_id",
        "parent_avail_id.reservation_line_ids",
        "parent_avail_id.reservation_line_ids.occupies_availability",
        "child_avail_ids",
        "child_avail_ids.reservation_line_ids",
        "child_avail_ids.reservation_line_ids.occupies_availability",
    )
    def _compute_real_avail(self):
        for record in self:
            Rooms = self.env["pms.room"]
            total_rooms = Rooms.search_count(
                [
                    ("active", "=", True),
                    ("room_type_id", "=", record.room_type_id.id),
                    ("pms_property_id", "=", record.pms_property_id.id),
                ]
            )
            room_ids = record.room_type_id.room_ids.filtered(
                lambda r, record=record: r.pms_property_id == record.pms_property_id
                and r.active
            ).ids
            count_rooms_not_avail = len(
                record.get_rooms_not_avail(
                    checkin=record.date,
                    checkout=record.date + datetime.timedelta(1),
                    room_ids=room_ids,
                    pms_property_id=record.pms_property_id.id,
                )
            )
            record.real_avail = total_rooms - count_rooms_not_avail

    @api.depends("reservation_line_ids", "reservation_line_ids.room_id")
    def _compute_parent_avail_id(self):
        for record in self:
            parent_rooms = record.room_type_id.mapped("room_ids.parent_id")
            if parent_rooms:
                parent_room_ids = parent_rooms.filtered(
                    lambda r, record=record: r.pms_property_id == record.pms_property_id
                ).ids
                for room_id in parent_room_ids:
                    room = self.env["pms.room"].browse(room_id)
                    parent_avail = self.env["pms.availability"].search(
                        [
                            ("date", "=", record.date),
                            ("room_type_id", "=", room.room_type_id.id),
                            ("pms_property_id", "=", record.pms_property_id.id),
                        ]
                    )
                    if parent_avail:
                        record.parent_avail_id = parent_avail
                    else:
                        record.parent_avail_id = self.env["pms.availability"].create(
                            {
                                "date": record.date,
                                "room_type_id": room.room_type_id.id,
                                "pms_property_id": record.pms_property_id.id,
                            }
                        )

    @api.depends("reservation_line_ids", "reservation_line_ids.room_id")
    def _compute_child_avail_ids(self):
        for record in self:
            child_rooms = record.room_type_id.mapped("room_ids.child_ids")
            if child_rooms:
                child_room_ids = child_rooms.filtered(
                    lambda r, record=record: r.pms_property_id == record.pms_property_id
                ).ids
                for room_id in child_room_ids:
                    room = self.env["pms.room"].browse(room_id)
                    child_avail = self.env["pms.availability"].search(
                        [
                            ("date", "=", record.date),
                            ("room_type_id", "=", room.room_type_id.id),
                            ("pms_property_id", "=", record.pms_property_id.id),
                        ]
                    )
                    if child_avail:
                        record.child_avail_ids = [(4, child_avail.id)]
                    else:
                        record.child_avail_ids = [
                            (
                                0,
                                0,
                                {
                                    "date": record.date,
                                    "room_type_id": room.room_type_id.id,
                                    "pms_property_id": record.pms_property_id.id,
                                },
                            )
                        ]

    @api.model
    def get_rooms_not_avail(
        self, checkin, checkout, room_ids, pms_property_id, current_lines=False
    ):
        RoomLines = self.env["pms.reservation.line"]
        rooms = self.env["pms.room"].browse(room_ids)
        occupied_room_ids = []
        for room in rooms.filtered("parent_id"):
            if self.get_occupied_parent_rooms(
                room=room.parent_id,
                checkin=checkin,
                checkout=checkout,
            ):
                occupied_room_ids.append(room.id)
        for room in rooms.filtered("child_ids"):
            if self.get_occupied_child_rooms(
                rooms=room.child_ids,
                checkin=checkin,
                checkout=checkout,
            ):
                occupied_room_ids.append(room.id)
        occupied_room_ids.extend(
            RoomLines.search(
                [
                    ("date", ">=", checkin),
                    ("date", "<=", checkout - datetime.timedelta(1)),
                    ("room_id", "in", room_ids),
                    ("pms_property_id", "=", pms_property_id),
                    ("occupies_availability", "=", True),
                    ("id", "not in", current_lines if current_lines else []),
                ]
            ).mapped("room_id.id")
        )
        return occupied_room_ids

    @api.model
    def get_occupied_parent_rooms(self, room, checkin, checkout):
        RoomLines = self.env["pms.reservation.line"]
        if (
            RoomLines.search_count(
                [
                    ("date", ">=", checkin),
                    ("date", "<=", checkout - datetime.timedelta(1)),
                    ("room_id", "=", room.id),
                    ("occupies_availability", "=", True),
                ]
            )
            > 0
        ):
            return True
        if room.parent_id:
            return self.get_occupied_parent_rooms(
                room=room.parent_id, checkin=checkin, checkout=checkout
            )
        return False

    @api.model
    def get_occupied_child_rooms(self, rooms, checkin, checkout):
        RoomLines = self.env["pms.reservation.line"]
        mapped_properties = list(set(rooms.mapped("pms_property_id.id")))
        if len(mapped_properties) > 1:
            raise ValidationError(_("Rooms shared between different properties"))

        if (
            RoomLines.search_count(
                [
                    ("date", ">=", checkin),
                    ("date", "<=", checkout - datetime.timedelta(1)),
                    ("room_id", "in", rooms.ids),
                    ("occupies_availability", "=", True),
                ]
            )
            > 0
        ):
            return True
        for room in rooms.filtered("child_ids"):
            if self.get_occupied_child_rooms(
                rooms=room.child_ids,
                checkin=checkin,
                checkout=checkout,
            ):
                return True
        return False

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
