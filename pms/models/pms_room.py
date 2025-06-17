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
    active = fields.Boolean(help="Determines if room is active", default=True)
    sequence = fields.Integer(
        help="Field used to change the position of the rooms in tree view."
        "Changing the position changes the sequence",
        default=0,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=True,
        comodel_name="pms.property",
        index=True,
        ondelete="restrict",
    )
    room_type_id = fields.Many2one(
        string="Property Room Type",
        help="Unique room type for the rooms",
        required=True,
        comodel_name="pms.room.type",
        ondelete="restrict",
        index=True,
        check_pms_properties=True,
    )
    parent_id = fields.Many2one(
        string="Parent Room",
        help="Indicates that this room is a child of another room",
        comodel_name="pms.room",
        ondelete="restrict",
        index=True,
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
        index=True,
        check_pms_properties=True,
    )
    capacity = fields.Integer(
        help="The maximum number of people that can occupy a room"
    )
    extra_beds_allowed = fields.Integer(
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

    short_name = fields.Char(
        help="Four character name, if not set, autocompletes with the first two "
        "letters of the room name and two incremental numbers",
    )
    address_is_independent = fields.Boolean(
        help="Indicates that the address of the room is independent of the property",
    )
    address_id = fields.Many2one(
        string="Address",
        help="Address of the room",
        comodel_name="res.partner",
        index=True,
        compute="_compute_address_id",
        store=True,
        ondelete="restrict",
    )
    street = fields.Char(
        related="address_id.street",
        readonly=False,
    )
    street2 = fields.Char(
        related="address_id.street2",
        readonly=False,
    )
    zip = fields.Char(
        related="address_id.zip",
        readonly=False,
    )
    city = fields.Char(
        related="address_id.city",
        readonly=False,
    )
    state_id = fields.Many2one(
        "res.country.state",
        related="address_id.state_id",
        string="State",
        ondelete="restrict",
        domain="[('country_id', '=?', country_id)]",
        readonly=False,
    )
    country_id = fields.Many2one(
        "res.country",
        related="address_id.country_id",
        string="Country",
        ondelete="restrict",
        readonly=False,
    )
    partner_latitude = fields.Float(
        string="Geo Latitude",
        related="address_id.partner_latitude",
        readonly=False,
        digits=(16, 5),
    )
    partner_longitude = fields.Float(
        string="Geo Longitude",
        related="address_id.partner_longitude",
        readonly=False,
        digits=(16, 5),
    )
    email = fields.Char(
        related="address_id.email",
        readonly=False,
    )
    email_formatted = fields.Char(
        "Formatted Email",
        compute="_compute_email_formatted",
        help='Format email address "Name <email@domain>"',
    )
    phone = fields.Char(
        related="address_id.phone",
        readonly=False,
    )
    mobile = fields.Char(
        related="address_id.mobile",
        readonly=False,
    )
    website = fields.Char(
        related="address_id.website",
        readonly=False,
    )
    image_1920 = fields.Image(
        related="address_id.image_1920",
        readonly=False,
        max_width=1920,
        max_height=1920,
    )

    _sql_constraints = [
        (
            "room_property_unique",
            "unique(name, pms_property_id)",
            "You cannot have more than one room "
            "with the same name in the same property",
        ),
        (
            "room_short_name_unique",
            "unique(short_name, pms_property_id)",
            "You cannot have more than one room "
            "with the same short name in the same property",
        ),
    ]

    @api.depends("child_ids")
    def _compute_is_shared_room(self):
        for record in self:
            record.is_shared_room = bool(record.child_ids)

    @api.depends("address_is_independent")
    def _compute_address_id(self):
        for record in self:
            if not record.address_is_independent:
                if record.address_id and record.address_id.active:
                    record.address_id.active = False
            if record.address_is_independent:
                if record.address_id and not record.address_id.active:
                    record.address_id.active = True
                elif not record.address_id:
                    record.address_id = (
                        self.env["res.partner"]
                        .with_context(avoid_document_restriction=True)
                        .create(
                            {
                                "name": record.name,
                                "type": "other",
                                "is_company": False,
                                "active": True,
                                "parent_id": record.pms_property_id.id,
                            }
                        )
                    )

    @api.depends("name", "email")
    def _compute_email_formatted(self):
        for room in self.filtered("address_id"):
            room.email_formatted = (
                room.address_id.email_formatted() if room.address_id else False
            )

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
                    lambda x, line=line: x.date == line.date
                    and x.product_id.is_extra_bed is True
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

    @api.constrains("short_name")
    def _check_short_name(self):
        for record in self:
            if len(record.short_name) > 4:
                raise ValidationError(
                    _("The short name can't contain more than 4 characters")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name") and not vals.get("short_name"):
                if len(vals["name"]) > 4:
                    short_name = self.calculate_short_name(vals)
                    vals.update({"short_name": short_name})
                else:
                    vals.update({"short_name": vals["name"]})
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("name") and not vals.get("short_name"):
            if len(vals["name"]) > 4:
                short_name = self.calculate_short_name(vals)
                vals.update({"short_name": short_name})
            else:
                vals.update({"short_name": vals["name"]})
        return super().write(vals)

    def calculate_short_name(self, vals):
        short_name = vals["name"][:2].upper()
        pms_property_id = self.pms_property_id.id
        if vals.get("pms_property_id"):
            pms_property_id = vals["pms_property_id"]
        rooms = self.env["pms.room"].search([("pms_property_id", "=", pms_property_id)])
        same_name_rooms = rooms.filtered(
            lambda room: room.name[:2].upper() == short_name
        )
        numbers_name = [0]
        for room in same_name_rooms:
            if room.short_name and room.short_name[:2] == short_name:
                if all(character.isdigit() for character in room.short_name[2:4]):
                    numbers_name.append(int(room.short_name[2:4]))
        max_number = max(numbers_name) + 1
        if max_number < 10:
            max_number = str(max_number).zfill(2)
        short_name += str(max_number)
        return str(short_name)

    # Business methods

    def get_capacity(self, extra_bed=0):
        for record in self:
            if extra_bed > record.extra_beds_allowed:
                raise ValidationError(
                    _("Extra beds can't be greater than allowed beds for this room")
                )
            return record.capacity + extra_bed
