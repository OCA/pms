# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsSharedRoom(models.Model):
    _name = "pms.shared.room"
    _description = "Shared Room"
    _order = "room_type_id, name"

    # Fields declaration
    name = fields.Char("Room Name", required=True)
    room_type_id = fields.Many2one(
        "pms.room.type",
        "Room Type",
        required=True,
        ondelete="restrict",
        domain=[("shared_room", "=", True)],
    )
    pms_property_id = fields.Many2one(
        "pms.property",
        store=True,
        readonly=True,
        related="room_type_id.pms_property_id",
    )
    floor_id = fields.Many2one(
        "pms.floor",
        "Ubication",
        ondelete="restrict",
        help="At which floor the room is located.",
    )
    bed_ids = fields.One2many(
        "pms.room",
        "shared_room_id",
        readonly=True,
    )
    active = fields.Boolean("Active", default=True)
    sequence = fields.Integer("Sequence", required=True)
    beds = fields.Integer("Beds")
    description_sale = fields.Text(
        "Sale Description",
        translate=True,
        help="A description of the Product that you want to communicate to "
        " your customers. This description will be copied to every Sales "
        " Order, Delivery Order and Customer Invoice/Credit Note",
    )

    # Constraints and onchanges
    @api.constrains("beds")
    def _constrain_beds(self):
        self.ensure_one()
        if self.beds < 1:
            raise ValidationError(_("Room beds can't be less than one"))
        if len(self.bed_ids) > self.beds:
            raise ValidationError(
                _(
                    "If you want to eliminate beds in the \
                room you must deactivate the beds from your form"
                )
            )
        beds = []
        inactive_beds = self.env["pms.room"].search(
            [("active", "=", False), ("shared_room_id", "=", self.id)]
        )
        for i in range(len(self.bed_ids), self.beds):
            if inactive_beds:
                bed = inactive_beds[0]
                bed.update({"active": True})
                inactive_beds -= bed
                continue
            name = u"{} ({})".format(self.name, i + 1)
            bed_vals = {
                "name": name,
                "capacity": 1,
                "room_type_id": self.room_type_id.id,
                "sequence": self.sequence,
                "floor_id": self.floor_id.id if self.floor_id else False,
                "shared_room_id": self.id,
            }
            beds.append((0, False, bed_vals))
        if beds:
            self.update({"bed_ids": beds})

    @api.constrains("active")
    def _constrain_active(self):
        self.bed_ids.write(
            {
                "active": self.active,
            }
        )

    @api.constrains("room_type_id")
    def _constrain_room_type_id(self):
        self.bed_ids.write(
            {
                "room_type_id": self.room_type_id.id,
            }
        )

    @api.constrains("floor_id")
    def _constrain_floor_id(self):
        self.bed_ids.write(
            {
                "floor_id": self.floor_id.id,
            }
        )

    @api.constrains("sequence")
    def _constrain_sequence(self):
        self.bed_ids.write(
            {
                "sequence": self.sequence,
            }
        )

    @api.constrains("descrition_sale")
    def _constrain_descrition_sale(self):
        self.bed_ids.write(
            {
                "description_sale": self.descrition_sale,
            }
        )
