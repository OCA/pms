# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoomType(models.Model):
    """Before creating a 'room type', you need to consider the following:
    With the term 'room type' is meant a sales type of residential accommodation: for
    example, a Double Room, a Economic Room, an Apartment, a Tent, a Caravan...
    """

    _name = "pms.room.type"
    _description = "Room Type"
    _inherits = {"product.product": "product_id"}
    _order = "sequence,default_code,name"
    _check_pms_properties_auto = True

    sequence = fields.Integer(
        string="Sequence",
        help="Field used to change the position of the room types in tree view.",
        default=0,
    )
    product_id = fields.Many2one(
        string="Product Room Type",
        help="Product identifier associated with room type",
        comodel_name="product.product",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    room_ids = fields.One2many(
        string="Rooms",
        help="Rooms that belong to room type.",
        comodel_name="pms.room",
        inverse_name="room_type_id",
        check_pms_properties=True,
    )
    class_id = fields.Many2one(
        string="Property Type Class",
        help="Class to which the room type belongs",
        comodel_name="pms.room.type.class",
        required=True,
        check_pms_properties=True,
    )
    board_service_room_type_ids = fields.One2many(
        string="Board Services",
        help="Board Service included in room type",
        comodel_name="pms.board.service.room.type",
        inverse_name="pms_room_type_id",
        check_pms_properties=True,
    )
    room_amenity_ids = fields.Many2many(
        string="Room Type Amenities",
        help="List of amenities included in room type",
        comodel_name="pms.amenity",
        relation="pms_room_type_amenity_rel",
        column1="room_type_id",
        column2="amenity_id",
        check_pms_properties=True,
    )
    default_code = fields.Char(
        string="Code",
        help="Identification code for a room type",
        required=True,
    )
    # TODO: Session review to define shared room and "sales rooms packs"
    is_shared_room = fields.Boolean(
        string="Shared Room",
        help="This room type is reservation by beds",
        default=False,
    )
    total_rooms_count = fields.Integer(
        string="Total Rooms Count",
        help="The number of rooms in a room type",
        compute="_compute_total_rooms_count",
        store=True,
    )
    default_max_avail = fields.Integer(
        string="Default Max. Availability",
        help="Maximum simultaneous availability on own Booking Engine "
        "given no availability rules. "
        "Use `-1` for using maximum simultaneous availability.",
        default=-1,
    )
    default_quota = fields.Integer(
        string="Default Quota",
        help="Quota assigned to the own Booking Engine given no availability rules. "
        "Use `-1` for managing no quota.",
        default=-1,
    )

    def name_get(self):
        result = []
        for room_type in self:
            name = room_type.name
            if self._context.get("checkin") and self._context.get("checkout"):
                pms_property = self.env["pms.property"].browse(
                    self._context.get("pms_property_id")
                )
                pms_property = pms_property.with_context(
                    checkin=self._context.get("checkin"),
                    checkout=self._context.get("checkout"),
                    room_type_id=room_type.id,
                    pricelist_id=self._context.get("pricelist_id") or False,
                )
                avail = pms_property.availability
                name += " (%s)" % avail
            result.append((room_type.id, name))
        return result

    @api.depends("room_ids", "room_ids.active")
    def _compute_total_rooms_count(self):
        for record in self:
            record.total_rooms_count = len(record.room_ids)

    @api.model
    def get_room_types_by_property(self, pms_property_id, default_code=None):
        """
        :param pms_property_id: property ID
        :param default_code: room type code (optional)
        :return: - recordset of
                    - all the pms.room.type of the pms_property_id
                      if default_code not defined
                    - one or 0 pms.room.type if default_code defined
                 - ValidationError if more than one default_code found by
                   the same pms_property_id
        """
        domain = []
        if default_code:
            domain += ["&", ("default_code", "=", default_code)]
        company_id = self.env["pms.property"].browse(pms_property_id).company_id.id
        domain += [
            "|",
            ("pms_property_ids", "in", pms_property_id),
            "|",
            "&",
            ("pms_property_ids", "=", False),
            ("company_id", "=", company_id),
            "&",
            ("pms_property_ids", "=", False),
            ("company_id", "=", False),
        ]
        records = self.search(domain)
        res, res_priority = {}, {}
        for rec in records:
            res_priority.setdefault(rec.default_code, -1)
            priority = (rec.pms_property_ids and 2) or (rec.company_id and 1 or 0)
            if priority > res_priority[rec.default_code]:
                res.setdefault(rec.default_code, rec.id)
                res[rec.default_code], res_priority[rec.default_code] = rec.id, priority
            elif priority == res_priority[rec.default_code]:
                raise ValidationError(
                    _(
                        "Integrity error: There's multiple room types "
                        "with the same code %s and properties"
                    )
                    % rec.default_code
                )
        return self.browse(list(res.values()))

    @api.constrains("default_code", "pms_property_ids", "company_id")
    def _check_code_property_company_uniqueness(self):
        msg = _("Already exists another room type with the same code and properties")
        for rec in self:
            if not rec.pms_property_ids:
                if self.search(
                    [
                        ("id", "!=", rec.id),
                        ("default_code", "=", rec.default_code),
                        ("pms_property_ids", "=", False),
                        ("company_id", "=", rec.company_id.id),
                    ]
                ):
                    raise ValidationError(msg)
            else:
                for pms_property in rec.pms_property_ids:
                    other = rec.get_room_types_by_property(
                        pms_property.id, rec.default_code
                    )
                    if other and other != rec:
                        raise ValidationError(msg)

    # ORM Overrides
    # TODO: Review Check product fields default values to room
    @api.model
    def create(self, vals):
        """ Add room types as not purchase services. """
        vals.update(
            {
                "purchase_ok": False,
                "sale_ok": False,
                "type": "service",
            }
        )
        return super().create(vals)

    # def unlink(self):
    #     for record in self:
    #         record.product_id.unlink()
    #     return super().unlink()

    def get_capacity(self):
        self.ensure_one()
        capacities = self.room_ids.mapped("capacity")
        return min(capacities) if any(capacities) else 0
