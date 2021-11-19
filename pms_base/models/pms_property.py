# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from odoo.addons.base.models.res_partner import _tz_get


class PmsProperty(models.Model):
    _name = "pms.property"
    _description = "Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {"res.partner": "partner_id"}

    def _default_team_id(self):
        return self.env.ref("pms_base.pms_team_default", raise_if_not_found=False)

    partner_id = fields.Many2one(
        string="Property",
        help="Current property",
        comodel_name="res.partner",
        required=True,
        ondelete="cascade",
    )
    owner_id = fields.Many2one(
        string="Owner",
        help="The owner of the property.",
        comodel_name="res.partner",
        required=True,
    )
    parent_id = fields.Many2one(string="Parent Property", comodel_name="pms.property")
    property_child_ids = fields.One2many(
        "pms.property", "parent_id", string="Children Property"
    )
    company_id = fields.Many2one(string="Company", comodel_name="res.company")
    team_id = fields.Many2one(
        "pms.team", string="Team", default=lambda self: self._default_team_id()
    )
    room_ids = fields.One2many(
        string="Rooms",
        help="List of rooms in the property.",
        comodel_name="pms.room",
        inverse_name="property_id",
    )
    room_count = fields.Integer(string="Number of rooms", compute="_compute_room_count")
    amenity_ids = fields.Many2many(
        string="Amenities",
        help="Amenities available in this property",
        comodel_name="pms.amenity",
        ondelete="restrict",
        relation="pms_property_amenity_rel",
        column1="property_id",
        column2="amenity_id",
    )
    service_ids = fields.One2many(
        string="Services",
        help="List of services available in the property.",
        comodel_name="pms.service",
        inverse_name="property_id",
    )
    tag_ids = fields.Many2many(
        string="Tags",
        comodel_name="pms.tag",
        relation="pms_property_tag_rel",
        column1="property_id",
        column2="tag_id",
    )
    tz = fields.Selection(
        string="Timezone",
        help="This field is used to determine the timezone of the property.",
        required=True,
        default=lambda self: self.env.user.tz or "UTC",
        selection=_tz_get,
    )
    area = fields.Float(string="Area")
    heating = fields.Selection(
        string="Heating",
        selection=[
            ("tankless_gas", "Gas (Tankless)"),
            ("boiler_gas", "Gas Boiler"),
            ("tankless_electric", "Electric (Tankless)"),
            ("boiler_electric", "Electric Boiler"),
            ("boiler_building", "Building Boiler"),
        ],
    )
    childs_property_count = fields.Integer(
        "Children Count", compute="_compute_childs_property"
    )
    floors_num = fields.Integer(string="Floor")
    unit_floor = fields.Integer(string="Unit Floor")
    balcony = fields.Boolean(string="Balcony", compute="_compute_balcony", store=True)
    laundry_room = fields.Boolean(
        string="Laundry Room", compute="_compute_laundry_room", store=True
    )
    parking_lot = fields.Boolean(
        string="Parking Lot", compute="_compute_parking_lot", store=True
    )
    pets = fields.Boolean(string="Pets", compute="_compute_pets", store=True)
    terrace = fields.Boolean(string="Terrace", compute="_compute_terrace", store=True)
    qty_half_bathroom = fields.Integer(
        string="Qty Half Bathroom", compute="_compute_qty_half_bathroom", store=True
    )
    qty_living_room = fields.Integer(
        string="Qty Living Room", compute="_compute_qty_living_room", store=True
    )
    qty_dining_room = fields.Integer(
        string="Qty Dining Room", compute="_compute_qty_dining_room", store=True
    )
    qty_kitchen = fields.Integer(
        string="Qty Kitchen", compute="_compute_qty_kitchen", store=True
    )
    qty_bedroom = fields.Integer(
        string="Qty Bedroom", compute="_compute_qty_bedroom", store=True
    )

    @api.depends("property_child_ids")
    def _compute_childs_property(self):
        for rec in self:
            rec.childs_property_count = len(rec.property_child_ids)

    @api.depends("room_ids")
    def _compute_room_count(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)

    @api.depends("room_ids")
    def _compute_balcony(self):
        for rec in self:
            type_id = self.env.ref(
                "pms_base.pms_room_type_balcony", raise_if_not_found=False
            )
            balcony = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))
            if balcony:
                rec.balcony = True
            else:
                rec.balcony = False

    @api.depends("room_ids", "amenity_ids")
    def _compute_laundry_room(self):
        for rec in self:
            room_type_id = self.env.ref(
                "pms_base.pms_room_type_laundry", raise_if_not_found=False
            )
            amenity_type_id = self.env.ref(
                "pms_base.pms_amenity_type_3", raise_if_not_found=False
            )
            room_count_laundry = len(
                rec.room_ids.filtered(lambda x: x.type_id == room_type_id)
            )
            amenity_count_laundry = len(
                rec.amenity_ids.filtered(lambda x: x.type_id == amenity_type_id)
            )
            if room_count_laundry or amenity_count_laundry:
                rec.laundry_room = True
            else:
                rec.laundry_room = False

    @api.depends("room_ids", "amenity_ids")
    def _compute_parking_lot(self):
        for rec in self:
            room_type_id = self.env.ref(
                "pms_base.pms_room_type_parking_lot", raise_if_not_found=False
            )
            amenity_type_id = self.env.ref(
                "pms_base.pms_amenity_type_4", raise_if_not_found=False
            )
            room_count_parking = len(
                rec.room_ids.filtered(lambda x: x.type_id == room_type_id)
            )
            amenity_count_parking = len(
                rec.amenity_ids.filtered(lambda x: x.type_id == amenity_type_id)
            )
            if room_count_parking or amenity_count_parking:
                rec.parking_lot = True
            else:
                rec.parking_lot = False

    @api.depends("room_ids", "amenity_ids")
    def _compute_pets(self):
        for rec in self:
            room_type_id = self.env.ref(
                "pms_base.pms_room_type_pets", raise_if_not_found=False
            )
            amenity_type_id = self.env.ref(
                "pms_base.pms_amenity_type_5", raise_if_not_found=False
            )
            room_count_pets = len(
                rec.room_ids.filtered(lambda x: x.type_id == room_type_id)
            )
            amenity_count_pets = len(
                rec.amenity_ids.filtered(lambda x: x.type_id == amenity_type_id)
            )
            if room_count_pets or amenity_count_pets:
                rec.pets = True
            else:
                rec.pets = False

    @api.depends("room_ids")
    def _compute_terrace(self):
        for rec in self:
            type_id = self.env.ref(
                "pms_base.pms_room_type_patio", raise_if_not_found=False
            )
            terrace = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))
            if terrace:
                rec.terrace = True
            else:
                rec.terrace = False

    @api.depends("room_ids")
    def _compute_qty_half_bathroom(self):
        for rec in self:
            type_id = self.env.ref(
                "pms_base.pms_room_type_half_bath", raise_if_not_found=False
            )
            rec.qty_half_bathroom = len(
                rec.room_ids.filtered(lambda x: x.type_id == type_id)
            )

    @api.depends("room_ids")
    def _compute_qty_living_room(self):
        for rec in self:
            type_id = self.env.ref(
                "pms_base.pms_room_type_living", raise_if_not_found=False
            )
            rec.qty_living_room = len(
                rec.room_ids.filtered(lambda x: x.type_id == type_id)
            )

    @api.depends("room_ids")
    def _compute_qty_dining_room(self):
        for rec in self:
            type_id = self.env.ref(
                "pms_base.pms_room_type_dining", raise_if_not_found=False
            )
            rec.qty_dining_room = len(
                rec.room_ids.filtered(lambda x: x.type_id == type_id)
            )

    @api.depends("room_ids")
    def _compute_qty_kitchen(self):
        for rec in self:
            type_id = self.env.ref(
                "pms_base.pms_room_type_kitchen", raise_if_not_found=False
            )
            rec.qty_kitchen = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))

    @api.depends("room_ids")
    def _compute_qty_bedroom(self):
        for rec in self:
            type_id = self.env.ref(
                "pms_base.pms_room_type_bed", raise_if_not_found=False
            )
            rec.qty_bedroom = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))

    def action_view_childs_property_list(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pms_base.action_pms_property"
        )
        action["domain"] = [("id", "in", self.property_child_ids.ids)]
        return action

    @api.model
    def create(self, vals):
        vals.update({"is_property": True})
        return super(PmsProperty, self).create(vals)

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(["name", "ref"])
        return [
            (
                property.id,
                "%s%s" % (property.ref and "[%s] " % property.ref or "", property.name),
            )
            for property in self
        ]

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("name", operator, name), ("ref", operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
