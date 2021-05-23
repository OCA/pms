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
        check_pms_properties=True,
    )
    room_type_id = fields.Many2one(
        string="Property Room Type",
        help="Unique room type for the rooms",
        required=True,
        comodel_name="pms.room.type",
        ondelete="restrict",
        check_pms_properties=True,
    )
    # TODO: design shared rooms
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
    description_sale = fields.Text(
        string="Sale Description",
        help="A description of the Product that you want to communicate to "
        " your customers. This description will be copied to every Sales "
        " Order, Delivery Order and Customer Invoice/Credit Note",
        translate=True,
    )
    occupation_status = fields.Selection(
        string="Room Status",
        selection=[
            ("occupied", "Occupied"),
            ("free", "Free"),
            ("out_service", "Out of service"),
        ],
        help="Room status based on occupancy, next arrival, or out of service",
        compute="_compute_occupation_status",
    )
    next_departure_reservation_id = fields.Many2one(
        string="Currently reservation",
        comodel_name="pms.reservation",
        help="Reservation that currently occupies the room",
        compute="_compute_occupation_status",
    )
    next_departure_datetime = fields.Datetime(
        string="Next departure",
        help="Expected departure from the reservation " "currently occupying the room",
        compute="_compute_occupation_status",
    )
    next_arrival_reservation_id = fields.Many2one(
        string="Next Reservation",
        comodel_name="pms.reservation",
        help="Next expected reservation",
        compute="_compute_next_arrival",
    )
    next_arrival_datetime = fields.Datetime(
        string="Next arrival",
        help="Next expected arrival date",
        compute="_compute_next_arrival",
    )
    color = fields.Integer(
        string="Color Index",
        default=1,
    )

    _sql_constraints = [
        (
            "room_property_unique",
            "unique(name, pms_property_id)",
            "you cannot have more than one room "
            "with the same name in the same property",
        )
    ]

    def _compute_occupation_status(self):
        for record in self:
            # Set Status and next departure fields
            current_reservation = (
                self.env["pms.reservation.line"]
                .search(
                    [
                        ("state", "in", ("onboard", "departure_delayed")),
                        ("room_id", "=", record.id),
                    ]
                )
                .reservation_id
            )

            record.occupation_status = "free"
            record.next_departure_datetime = False
            record.next_departure_reservation_id = False

            if current_reservation:
                record.occupation_status = "occupied"
                record.next_departure_reservation_id = current_reservation
                record.next_departure_datetime = current_reservation.checkout_datetime
                if current_reservation.reservation_type == "out_service":
                    record.occupation_status = "out_service"

    def _compute_next_arrival(self):
        today = fields.Date.today()
        for record in self:
            future_reservation_dates = (
                self.env["pms.reservation.line"]
                .search(
                    [
                        ("state", "in", ("draft", "confirm", "arrival_delayed")),
                        ("room_id", "=", record.id),
                        ("date", ">=", today),
                    ]
                )
                .mapped("date")
            )

            record.next_arrival_reservation_id = (
                self.env["pms.reservation.line"]
                .search(
                    [
                        ("room_id", "=", record.id),
                        ("date", "=", min(future_reservation_dates)),
                    ]
                )
                .reservation_id
            )

            record.next_arrival_datetime = (
                record.next_arrival_reservation_id.checkin_datetime
                if record.next_arrival_reservation_id
                else False
            )

    def name_get(self):
        result = []
        for room in self:
            name = room.name
            if room.room_type_id:
                name += " [%s]" % room.room_type_id.default_code
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

    # Business methods

    def get_capacity(self, extra_bed=0):
        for record in self:
            if not record.shared_room_id:
                if extra_bed > record.extra_beds_allowed:
                    raise ValidationError(
                        _("Extra beds can't be greater than allowed beds for this room")
                    )
                return record.capacity + extra_bed
            return record.capacity
