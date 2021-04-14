# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoom(models.Model):
    """The rooms for lodging can be for sleeping, usually called rooms,
    and also for speeches (conference rooms), parking,
    relax with cafe con leche, spa...
    """

    _name = "pms.room"
    _description = "Property Room"
    _order = "sequence, room_type_id, name"

    name = fields.Char(
        string="Room Name",
        help="Room Name",
        required=True,
    )
    active = fields.Boolean(
        string="Active", help="Determines if room is active", default=True
    )
    sequence = fields.Integer(
        string="Sequence",
        help="Field used to change the position of the rooms in tree view."
        "Changing the position changes the sequence",
        default=0,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=True,
        default=lambda self: self.env.user.active_property_ids[0],
        comodel_name="pms.property",
        ondelete="restrict",
    )
    room_type_id = fields.Many2one(
        string="Property Room Type",
        help="Unique room type for the rooms",
        required=True,
        comodel_name="pms.room.type",
        domain=[
            "|",
            ("pms_property_ids", "=", False),
            (pms_property_id, "in", "pms_property_ids"),
        ],
        ondelete="restrict",
    )
    # TODO: Dario, design shared rooms
    shared_room_id = fields.Many2one(
        string="Shared Room",
        help="The room can be sold by beds",
        default=False,
        comodel_name="pms.shared.room",
    )
    ubication_id = fields.Many2one(
        string="Ubication",
        help="At which ubication the room is located.",
        comodel_name="pms.ubication",
        domain=[
            "|",
            ("pms_property_ids", "=", False),
            (pms_property_id, "in", "pms_property_ids"),
        ],
    )
    capacity = fields.Integer(
        string="Capacity", help="The maximum number of people that can occupy a room"
    )
    extra_beds_allowed = fields.Integer(
        string="Extra Beds Allowed",
        help="Number of extra beds allowed in room",
        required=True,
        default="0",
    )
    description_sale = fields.Text(
        string="Sale Description",
        help="A description of the Product that you want to communicate to "
        " your customers. This description will be copied to every Sales "
        " Order, Delivery Order and Customer Invoice/Credit Note",
        translate=True,
    )

    allowed_property_ids = fields.Many2many(
        string="Allowed Properties",
        help="Allowed properties for rooms",
        store=True,
        readonly=True,
        compute="_compute_allowed_property_ids",
        comodel_name="pms.property",
        relation="room_property_rel",
        column1="room_id",
        column2="property_id",
    )

    def name_get(self):
        result = []
        for room in self:
            name = room.name
            if room.room_type_id:
                name += " [%s]" % room.room_type_id.default_code
            result.append((room.id, name))
        return result

    @api.depends(
        "room_type_id",
        "room_type_id.pms_property_ids",
        "ubication_id",
        "ubication_id.pms_property_ids",
    )
    # TODO: Dario, revisar flujo de allowed properties
    def _compute_allowed_property_ids(self):
        for record in self:
            if not (
                record.room_type_id.pms_property_ids
                or record.ubication_id.pms_property_ids
            ):
                record.allowed_property_ids = self.env["pms.property"].search([])
            elif not record.room_type_id.pms_property_ids:
                record.allowed_property_ids = record.ubication_id.pms_property_ids
            elif not record.ubication_id.pms_property_ids:
                record.allowed_property_ids = record.room_type_id.pms_property_ids
            else:
                record.allowed_property_ids = (
                    record.room_type_id.pms_property_ids
                    & record.ubication_id.pms_property_ids
                )

    @api.constrains("capacity")
    def _check_capacity(self):
        for record in self:
            if record.capacity < 1:
                raise ValidationError(
                    _(
                        "The capacity of the \
                        room must be greater than 0."
                    )
                )

    @api.constrains(
        "allowed_property_ids",
        "pms_property_id",
    )
    def _check_property_integrity(self):
        for rec in self:
            if rec.pms_property_id:
                if rec.pms_property_id.id not in rec.allowed_property_ids.ids:
                    raise ValidationError(
                        _("Property not allowed in room type or in ubication")
                    )

    def get_capacity(self, extra_bed=0):
        for record in self:
            if not record.shared_room_id:
                if extra_bed > record.extra_beds_allowed:
                    raise ValidationError(
                        _("Extra beds can't be greater than allowed beds for this room")
                    )
                return record.capacity + extra_bed
            return record.capacity
