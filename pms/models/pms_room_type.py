# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
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
    _order = "sequence, code_type, name"

    # Default methods
    @api.model
    def _get_default_pms_property(self):
        return self.env.user.pms_property_id

    # Fields declaration
    product_id = fields.Many2one(
        "product.product",
        "Product Room Type",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    pms_property_id = fields.Many2one(
        "pms.property",
        "Property",
        required=True,
        ondelete="restrict",
        default=_get_default_pms_property,
    )
    room_ids = fields.One2many("pms.room", "room_type_id", "Rooms")
    class_id = fields.Many2one("pms.room.type.class", "Property Type Class")
    board_service_room_type_ids = fields.One2many(
        "pms.board.service.room.type", "pms_room_type_id", string="Board Services"
    )
    room_amenity_ids = fields.Many2many(
        "pms.amenity",
        "pms_room_type_aminity_rel",
        "room_type_ids",
        "amenity_ids",
        string="Room Type Amenities",
        help="List of Amenities.",
    )
    code_type = fields.Char(
        "Code",
        required=True,
    )
    shared_room = fields.Boolean(
        "Shared Room", default=False, help="This room type is reservation by beds"
    )
    total_rooms_count = fields.Integer(compute="_compute_total_rooms", store=True)
    active = fields.Boolean("Active", default=True)
    sequence = fields.Integer("Sequence", default=0)
    default_max_avail = fields.Integer(
        "Max. Availability",
        default=-1,
        help="Maximum simultaneous availability on own Booking Engine "
        "given no availability rules. "
        "Use `-1` for using maximum simultaneous availability.",
    )
    default_quota = fields.Integer(
        "Default Quota",
        default=-1,
        help="Quota assigned to the own Booking Engine given no availability rules. "
        "Use `-1` for managing no quota.",
    )

    _sql_constraints = [
        (
            "code_type_pms_unique",
            "unique(code_type, pms_property_id)",
            "Room Type Code must be unique by Property!",
        ),
    ]

    # Constraints and onchanges
    @api.depends("room_ids", "room_ids.active")
    def _compute_total_rooms(self):
        for record in self:
            record.total_rooms_count = len(record.room_ids)

    # ORM Overrides
    @api.model
    def create(self, vals):
        """ Add room types as not purchase services. """
        vals.update(
            {
                "purchase_ok": False,
                "type": "service",
            }
        )
        return super().create(vals)

    def unlink(self):
        for record in self:
            record.product_id.unlink()
        return super().unlink()

    # Business methods

    def get_capacity(self):
        self.ensure_one()
        capacities = self.room_ids.mapped("capacity")
        return min(capacities) if any(capacities) else 0

    @api.model
    def get_rate_room_types(self, **kwargs):
        """
        room_type_ids: Ids from room types to get rate, optional, if you
            not use this param, the method return all room_types
        from: Date from, mandatory
        days: Number of days, mandatory
        pricelist_id: Pricelist to use, optional
        partner_id: Partner, optional
        Return Dict Code Room Types: subdict with day, discount, price
        """
        vals = {}
        # room_type_ids = kwargs.get("room_type_ids", False)
        # room_types = (
        #     self.env["pms.room.type"].browse(room_type_ids)
        #     if room_type_ids
        #     else self.env["pms.room.type"].search([])
        # )
        date_from = kwargs.get("date_from", False)
        days = kwargs.get("days", False)
        discount = kwargs.get("discount", False)
        if not date_from or not days:
            raise ValidationError(_("Date From and days are mandatory"))
        partner_id = kwargs.get("partner_id", False)
        # partner = self.env["res.partner"].browse(partner_id)
        # pricelist_id = kwargs.get(
        #     "pricelist_id",
        #     partner.property_product_pricelist.id
        #     and partner.property_product_pricelist.id
        #     or self.env.user.pms_property_id.default_pricelist_id.id,
        # )
        vals.update(
            {
                "partner_id": partner_id if partner_id else False,
                "discount": discount,
            }
        )
        rate_vals = {}
        # TODO: Now it is computed field, We need other way to return rates
        # for room_type in room_types:
        #     vals.update({"room_type_id": room_type.id})
        #     room_vals = self.env["pms.reservation"].prepare_reservation_lines(
        #         date_from,
        #         days,
        #         pricelist_id=pricelist_id,
        #         vals=vals,
        #         update_old_prices=False,
        #     )
        #     rate_vals.update(
        #         {
        #             room_type.id: [
        #                 item[2] for item in room_vals[
        #                   "reservation_line_ids"
        #                   ] if item[2]
        #             ]
        #         }
        #     )
        return rate_vals
