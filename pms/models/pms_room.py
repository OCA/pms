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

    # Defaults and Gets
    def name_get(self):
        result = []
        for room in self:
            name = room.name
            if room.room_type_id:
                name += " [%s]" % room.room_type_id.code_type
            result.append((room.id, name))
        return result

    # Fields declaration
    name = fields.Char("Room Name", required=True)
    pms_property_id = fields.Many2one(
        "pms.property",
        required=True,
        ondelete="restrict",
        default=lambda self: self.env.user.get_active_property_ids()[0],
    )
    room_type_id = fields.Many2one(
        "pms.room.type", "Property Room Type", required=True, ondelete="restrict"
    )
    shared_room_id = fields.Many2one("pms.shared.room", "Shared Room", default=False)
    floor_id = fields.Many2one(
        "pms.floor", "Ubication", help="At which floor the room is located."
    )
    capacity = fields.Integer("Capacity")
    to_be_cleaned = fields.Boolean("To be Cleaned", default=False)
    extra_beds_allowed = fields.Integer(
        "Extra beds allowed", default="0", required=True
    )
    description_sale = fields.Text(
        "Sale Description",
        translate=True,
        help="A description of the Product that you want to communicate to "
        " your customers. This description will be copied to every Sales "
        " Order, Delivery Order and Customer Invoice/Credit Note",
    )
    active = fields.Boolean("Active", default=True)
    sequence = fields.Integer("Sequence", default=0)

    allowed_property_ids = fields.Many2many(
        comodel_name="pms.property",
        relation="room_property_rel",
        column1="room_id",
        column2="property_id",
        string="Allowed properties",
        store=True,
        readonly=True,
        compute="_compute_allowed_property_ids",
    )

    @api.depends("room_type_id.pms_property_ids", "floor_id.pms_property_ids")
    def _compute_allowed_property_ids(self):
        for record in self:
            if not (
                record.room_type_id.pms_property_ids or record.floor_id.pms_property_ids
            ):
                record.allowed_property_ids = False
            else:
                if record.room_type_id.pms_property_ids:
                    if record.floor_id.pms_property_ids:
                        properties = list(
                            set(record.room_type_id.pms_property_ids.ids)
                            & set(record.floor_id.pms_property_ids.ids)
                        )
                        record.allowed_property_ids = self.env["pms.property"].search(
                            [("id", "in", properties)]
                        )
                    else:
                        record.allowed_property_ids = (
                            record.room_type_id.pms_property_ids
                        )
                else:
                    record.allowed_property_ids = record.floor_id.pms_property_ids

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

    @api.constrains(
        "allowed_property_ids",
        "pms_property_id",
    )
    def _check_property_integrity(self):
        for rec in self:
            if rec.pms_property_id and rec.allowed_property_ids:
                if rec.pms_property_id.id not in rec.allowed_property_ids.ids:
                    raise ValidationError(_("Property not allowed"))

    # Business methods

    def get_capacity(self, extra_bed=0):
        if not self.shared_room_id:
            return self.capacity + extra_bed
        return self.capacity
