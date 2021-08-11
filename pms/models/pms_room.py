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
    _check_pms_properties_auto = True

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
        default=lambda self: self.env.user.get_active_property_ids()[0],
        comodel_name="pms.property",
        ondelete="restrict",
    )
    room_type_id = fields.Many2one(
        string="Property Room Type",
        help="Unique room type for the rooms",
        required=True,
        comodel_name="pms.room.type",
        ondelete="restrict",
        check_pms_properties=True,
    )
    parent_id = fields.Many2one(
        string="Parent Room",
        help="Indicates that this room is a child of another room",
        comodel_name="pms.room",
        ondelete="restrict",
        check_pms_properties=True,
    )
    child_ids = fields.One2many(
        string="Child Rooms",
        help="Child rooms of the room",
        comodel_name="pms.room",
        inverse_name="parent_id",
        check_pms_properties=True,
    )
    ubication_id = fields.Many2one(
        string="Ubication",
        help="At which ubication the room is located.",
        comodel_name="pms.ubication",
        check_pms_properties=True,
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
    room_amenity_ids = fields.Many2many(
        string="Room Amenities",
        help="List of amenities included in room",
        comodel_name="pms.amenity",
        relation="pms_room_amenity_rel",
        column1="room_id",
        column2="amenity_id",
        check_pms_properties=True,
    )
    is_shared_room = fields.Boolean(
        string="Is a Shared Room",
        help="allows you to reserve units " " smaller than the room itself (eg beds)",
        compute="_compute_is_shared_room",
        readonly=False,
        store=True,
    )
    description_sale = fields.Text(
        string="Sale Description",
        help="A description of the Product that you want to communicate to "
        " your customers. This description will be copied to every Sales "
        " Order, Delivery Order and Customer Invoice/Credit Note",
        translate=True,
    )

    _sql_constraints = [
        (
            "room_property_unique",
            "unique(name, pms_property_id)",
            "you cannot have more than one room "
            "with the same name in the same property",
        )
    ]

    @api.depends("child_ids")
    def _compute_is_shared_room(self):
        for record in self:
            if record.child_ids:
                record.is_shared_room = True
            elif not record.is_shared_room:
                record.is_shared_room = False

    def name_get(self):
        result = []
        for room in self:
            name = room.name
            if room.room_type_id:
                name += " [%s]" % room.room_type_id.default_code
            if room.room_amenity_ids:
                for amenity in room.room_amenity_ids:
                    if amenity.is_add_code_room_name:
                        name += " %s" % amenity.default_code
            result.append((room.id, name))
        return result

    # Constraints and onchanges
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

    @api.constrains("is_shared_room")
    def _check_shared_room(self):
        for record in self:
            if record.is_shared_room and not record.child_ids:
                raise ValidationError(
                    _(
                        "The reservation units are required \
                        on shared rooms."
                    )
                )

    @api.model
    def _check_adults(self, reservation, service_line_ids=False):
        for line in reservation.reservation_line_ids:
            num_extra_beds = 0
            if service_line_ids:
                extra_beds = service_line_ids.filtered(
                    lambda x: x.date == line.date and x.product_id.is_extra_bed is True
                )
                num_extra_beds = sum(extra_beds.mapped("day_qty")) if extra_beds else 0
            if line.room_id:
                if (
                    reservation.adults + reservation.children_occupying
                ) > line.room_id.get_capacity(num_extra_beds):
                    raise ValidationError(
                        _(
                            "Persons can't be higher than room capacity (%s)",
                            reservation.name,
                        )
                    )

    # Business methods

    def get_capacity(self, extra_bed=0):
        for record in self:
            if extra_bed > record.extra_beds_allowed:
                raise ValidationError(
                    _("Extra beds can't be greater than allowed beds for this room")
                )
            return record.capacity + extra_bed
