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
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Room Name", help="Name of the shared room", required=True
    )
    active = fields.Boolean(
        string="Active", help="Determines if shared room is active", default=True
    )
    sequence = fields.Integer(
        string="Sequence",
        help="Field used to change the position of the shared rooms in tree view."
        "Changing the position changes the sequence",
        required=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room type which the shared room belongs",
        comodel_name="pms.room.type",
        required=True,
        ondelete="restrict",
        domain=[("shared_room", "=", True)],
    )
    # TODO: properties relation
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        relation="pms_shared_room_pms_property_rel",
        column1="shared_room_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    ubication_id = fields.Many2one(
        string="Ubication",
        help="At which ubication the room is located.",
        comodel_name="pms.ubication",
        ondelete="restrict",
    )
    bed_ids = fields.One2many(
        string="Beds",
        help="Beds in one room",
        comodel_name="pms.room",
        inverse_name="shared_room_id",
        readonly=True,
    )
    beds = fields.Integer(
        string="Number Of Beds", help="Number of beds in a shared room"
    )
    description_sale = fields.Text(
        string="Sale Description",
        help="A description of the Product that you want to communicate to "
        " your customers. This description will be copied to every Sales "
        " Order, Delivery Order and Customer Invoice/Credit Note",
        translate=True,
    )

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
                "ubication_id": self.ubication_id.id if self.ubication_id else False,
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

    @api.constrains("ubication_id")
    def _constrain_ubication_id(self):
        self.bed_ids.write(
            {
                "ubication_id": self.ubication_id.id,
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
