# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round


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
    # Room types a price can be derived through, from the priced one up to the
    # root of its chain
    _price_derivation_max_depth = 10

    sequence = fields.Integer(
        help="Field used to change the position of the room types in tree view.",
        default=0,
    )
    product_id = fields.Many2one(
        string="Product Room Type",
        help="Product identifier associated with room type",
        comodel_name="product.product",
        required=True,
        delegate=True,
        index=True,
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
        index=True,
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
    total_rooms_count = fields.Integer(
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
        help="Quota assigned to the own Booking Engine given no availability rules. "
        "Use `-1` for managing no quota.",
        default=-1,
    )
    overnight_room = fields.Boolean(
        related="class_id.overnight",
        store=True,
    )
    min_price = fields.Float(
        string="Min. Price",
        help="Minimum price for a room type",
        default=5.0,
    )
    price_base_room_type_id = fields.Many2one(
        string="Price Derived From",
        help="Room type whose price is the base of this one in the pricelists "
        "without a rule of their own for it",
        comodel_name="pms.room.type",
        ondelete="restrict",
        index=True,
        check_pms_properties=True,
    )
    price_derived_room_type_ids = fields.One2many(
        string="Derived Room Types",
        help="Room types whose price is derived from this one",
        comodel_name="pms.room.type",
        inverse_name="price_base_room_type_id",
        check_pms_properties=True,
    )
    price_derivation_type = fields.Selection(
        string="Price Variation Type",
        help="Whether the variation is a fixed amount or a percentage of the "
        "price of the base room type",
        selection=[("amount", "Fixed amount"), ("percent", "Percentage")],
        default="amount",
        required=True,
    )
    price_derivation_value = fields.Float(
        string="Price Variation",
        help="Added to the price of the base room type, as an amount in the "
        "currency of the pricelist or as a percentage of that price. Negative "
        "values lower it",
        digits="Product Price",
    )
    price_derivation_rounding = fields.Float(
        string="Price Rounding",
        help="Round the prices derived by a percentage to a multiple of this "
        "value, e.g. 1 for whole amounts. Zero rounds them to the currency",
        digits="Product Price",
    )
    price_derivation_pricelist_ids = fields.Many2many(
        string="Derive in Pricelists",
        help="Pricelists where the price is derived. Leave it empty to derive "
        "it in all of them",
        comodel_name="product.pricelist",
        relation="pms_room_type_price_derivation_pricelist_rel",
        column1="room_type_id",
        column2="pricelist_id",
        check_pms_properties=True,
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

    @api.constrains("price_base_room_type_id")
    def _check_price_base_room_type_id(self):
        """A price cannot be derived in a loop, nor through endless chains.

        Prices are derived on the fly, level by level, so a loop would never
        end and the engine refuses to follow chains longer than
        ``_price_derivation_max_depth``: refuse both when they are set up
        rather than when selling.
        """
        if not self._check_recursion(parent="price_base_room_type_id"):
            raise ValidationError(
                _(
                    "A room type cannot derive its price from itself, directly "
                    "or through other room types."
                )
            )
        # All of them, also the archived ones and the ones out of the access
        # of the current user
        room_types = self.sudo().with_context(active_test=False)
        for room_type in room_types | room_types._get_price_derivation_descendants():
            depth = room_type._get_price_derivation_depth()
            if depth > self._price_derivation_max_depth:
                raise ValidationError(
                    _(
                        "The price of %(room_type)s is derived through too many "
                        "levels.",
                        room_type=room_type.display_name,
                    )
                )

    @api.constrains(
        "price_derivation_type", "price_derivation_value", "price_derivation_rounding"
    )
    def _check_price_derivation_values(self):
        for room_type in self:
            if (
                room_type.price_derivation_type == "percent"
                and room_type.price_derivation_value <= -100
            ):
                raise ValidationError(
                    _("A percentage variation must be greater than -100%.")
                )
            if room_type.price_derivation_rounding < 0:
                raise ValidationError(_("The price rounding can't be negative."))

    # ORM Overrides
    # TODO: Review Check product fields default values to room
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.update(
                {
                    "purchase_ok": False,
                    "sale_ok": False,
                    "detailed_type": "service",
                }
            )
        return super().create(vals_list)

    # def unlink(self):
    #     for record in self:
    #         record.product_id.unlink()
    #     return super().unlink()

    def get_room_type_capacity(self, pms_property_id):
        """
        :param pms_property_id: int
        :return: the minimum capacity for rooms of current type
        """
        self.ensure_one()
        capacities = self.room_ids.filtered(
            lambda r: not r.pms_property_id or r.pms_property_id.id == pms_property_id
        ).mapped("capacity")
        return min(capacities) if any(capacities) else 0

    @api.model
    def get_default_board_service(self, pms_property_id, room_type_id, pricelist_id):
        board_services_candidates = self.env["pms.board.service.room.type"].search(
            [
                ("pms_room_type_id", "=", room_type_id),
                ("by_default", "=", True),
                ("pms_property_id", "=", pms_property_id),
            ]
        )
        board_service_default = (
            board_services_candidates.filtered(
                lambda service: pricelist_id in service.pricelist_ids.ids
            )
            or board_services_candidates.filtered(
                lambda service: not service.pricelist_ids
            )
            or False
        )
        return board_service_default

    def _get_price_derivation(self, pricelist):
        """The room types of self whose price is derived in the pricelist.

        A room type derives its price from its base room type in the
        pricelists it is set to derive in, or in all of them when none is set.
        This is only where the derivation applies: the engine still uses a
        rule of the pricelist covering the room type whenever there is one.
        Callers only rely on the result being empty or not, so the variation
        can come from elsewhere (e.g. a rule per pricelist) in the future.
        It is the same whoever asks: the configuration is read as stored.
        """
        if not pricelist:
            return self.browse()
        # Read as stored: neither the access of the current user to the
        # pricelists nor archiving them may empty a restriction, which would
        # make the room type derive in all the pricelists
        stored = self.sudo().with_context(active_test=False)
        return self & stored.filtered(
            lambda room_type: room_type.price_base_room_type_id
            and (
                not room_type.price_derivation_pricelist_ids
                or pricelist.id in room_type.price_derivation_pricelist_ids.ids
            )
        )

    def _derive_price(self, base_price, currency=None):
        """Apply the price variation of the room type to the price of its base.

        The variation is an amount, in the currency of the pricelist, or a
        percentage of the base price. Prices derived by a percentage are
        rounded to the multiple set on the room type, if any, and the result
        to the currency. It never goes below zero.
        """
        self.ensure_one()
        if self.price_derivation_type == "percent":
            price = base_price * (1 + self.price_derivation_value / 100)
            if self.price_derivation_rounding:
                price = float_round(
                    price, precision_rounding=self.price_derivation_rounding
                )
        else:
            price = base_price + self.price_derivation_value
        if currency:
            price = currency.round(price)
        return max(price, 0.0)

    def _get_price_derivation_descendants(self):
        """The room types deriving their price from self, at any level.

        Breadth first, so every room type comes after the one its price is
        derived from. The room types of self are not part of the result.
        """
        descendants = self.browse()
        derived = self.price_derived_room_type_ids
        while derived:
            # Guard against loops written bypassing the constraints
            derived -= self | descendants
            descendants |= derived
            derived = derived.price_derived_room_type_ids
        return descendants

    def _get_price_derivation_depth(self):
        """How many room types the price goes through up to the root one.

        Counting stops past ``_price_derivation_max_depth``, which is all
        callers need to know and keeps it finite on loops.
        """
        self.ensure_one()
        depth = 0
        base_room_type = self.price_base_room_type_id
        while base_room_type and depth <= self._price_derivation_max_depth:
            depth += 1
            base_room_type = base_room_type.price_base_room_type_id
        return depth
