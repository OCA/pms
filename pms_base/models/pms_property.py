# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import _tz_get


class PmsProperty(models.Model):
    _name = "pms.property"
    _description = "Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {"res.partner": "partner_id"}

    def _default_team_id(self):
        return self.env.ref("pms_base.pms_team_default", raise_if_not_found=False)

    def _default_stage_id(self):
        stage = self.env["pms.stage"].search(
            [
                ("stage_type", "=", "property"),
                ("is_default", "=", True),
                ("company_id", "in", (self.env.company.id, False)),
            ],
            order="sequence asc",
            limit=1,
        )
        if stage:
            return stage
        raise ValidationError(_("You must create an property stage first."))

    partner_id = fields.Many2one(
        string="Property",
        help="Current property",
        comodel_name="res.partner",
        required=True,
        ondelete="cascade",
    )
    owner_id = fields.Many2one(
        help="The owner of the property.",
        comodel_name="res.partner",
        required=True,
    )
    stage_id = fields.Many2one(
        "pms.stage",
        string="Stage",
        group_expand="_read_group_stage_ids",
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: self._default_stage_id(),
    )
    parent_id = fields.Many2one(comodel_name="pms.property")
    property_child_ids = fields.One2many(
        "pms.property", "parent_id", string="Children Property"
    )
    company_id = fields.Many2one(comodel_name="res.company")
    team_id = fields.Many2one("pms.team", default=lambda self: self._default_team_id())
    room_ids = fields.One2many(
        help="List of rooms in the property.",
        comodel_name="pms.room",
        inverse_name="property_id",
    )
    room_count = fields.Integer(string="Number of rooms", compute="_compute_room_count")
    amenity_ids = fields.Many2many(
        help="Amenities available in this property",
        comodel_name="pms.amenity",
        ondelete="restrict",
        relation="pms_property_amenity_rel",
        column1="property_id",
        column2="amenity_id",
    )
    service_ids = fields.One2many(
        help="List of services available in the property.",
        comodel_name="pms.service",
        inverse_name="property_id",
    )
    tag_ids = fields.Many2many(
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
    area = fields.Float()
    heating = fields.Selection(
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
    unit_floor = fields.Integer()
    balcony = fields.Boolean(compute="_compute_balcony", store=True)
    laundry_room = fields.Boolean(compute="_compute_laundry_room", store=True)
    parking_lot = fields.Boolean(compute="_compute_parking_lot", store=True)
    pets = fields.Boolean(compute="_compute_pets", store=True)
    terrace = fields.Boolean(compute="_compute_terrace", store=True)
    qty_half_bathroom = fields.Integer(compute="_compute_qty_half_bathroom", store=True)
    qty_living_room = fields.Integer(compute="_compute_qty_living_room", store=True)
    qty_dining_room = fields.Integer(compute="_compute_qty_dining_room", store=True)
    qty_kitchen = fields.Integer(compute="_compute_qty_kitchen", store=True)
    qty_bedroom = fields.Integer(compute="_compute_qty_bedroom", store=True)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None):
        search_domain = [("stage_type", "=", "property")]
        if self.env.context.get("default_team_id"):
            search_domain = [
                "&",
                ("team_ids", "in", self.env.context["default_team_id"]),
            ] + search_domain
        return stages.search(search_domain, order=order)

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
        type_id = self.env.ref(
            "pms_base.pms_room_type_balcony", raise_if_not_found=False
        )
        for rec in self:
            rec.balcony = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))

    @api.depends("room_ids", "amenity_ids")
    def _compute_laundry_room(self):
        room_type_id = self.env.ref(
            "pms_base.pms_room_type_laundry", raise_if_not_found=False
        )
        amenity_type_id = self.env.ref(
            "pms_base.pms_amenity_type_3", raise_if_not_found=False
        )
        for rec in self:
            room_count_laundry = len(
                rec.room_ids.filtered(lambda x: x.type_id == room_type_id)
            )
            amenity_count_laundry = len(
                rec.amenity_ids.filtered(lambda x: x.type_id == amenity_type_id)
            )
            rec.laundry_room = room_count_laundry or amenity_count_laundry

    @api.depends("room_ids", "amenity_ids")
    def _compute_parking_lot(self):
        room_type_id = self.env.ref(
            "pms_base.pms_room_type_parking_lot", raise_if_not_found=False
        )
        amenity_type_id = self.env.ref(
            "pms_base.pms_amenity_type_4", raise_if_not_found=False
        )
        for rec in self:
            room_count_parking = len(
                rec.room_ids.filtered(lambda x: x.type_id == room_type_id)
            )
            amenity_count_parking = len(
                rec.amenity_ids.filtered(lambda x: x.type_id == amenity_type_id)
            )
            rec.parking_lot = room_count_parking or amenity_count_parking

    @api.depends("room_ids", "amenity_ids")
    def _compute_pets(self):
        room_type_id = self.env.ref(
            "pms_base.pms_room_type_pets", raise_if_not_found=False
        )
        amenity_type_id = self.env.ref(
            "pms_base.pms_amenity_type_5", raise_if_not_found=False
        )
        for rec in self:
            room_count_pets = len(
                rec.room_ids.filtered(lambda x: x.type_id == room_type_id)
            )
            amenity_count_pets = len(
                rec.amenity_ids.filtered(lambda x: x.type_id == amenity_type_id)
            )
            rec.pets = room_count_pets or amenity_count_pets

    @api.depends("room_ids")
    def _compute_terrace(self):
        type_id = self.env.ref("pms_base.pms_room_type_patio", raise_if_not_found=False)
        for rec in self:
            rec.terrace = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))

    @api.depends("room_ids")
    def _compute_qty_half_bathroom(self):
        type_id = self.env.ref(
            "pms_base.pms_room_type_half_bath", raise_if_not_found=False
        )
        for rec in self:
            rec.qty_half_bathroom = len(
                rec.room_ids.filtered(lambda x: x.type_id == type_id)
            )

    @api.depends("room_ids")
    def _compute_qty_living_room(self):
        type_id = self.env.ref(
            "pms_base.pms_room_type_living", raise_if_not_found=False
        )
        for rec in self:
            rec.qty_living_room = len(
                rec.room_ids.filtered(lambda x: x.type_id == type_id)
            )

    @api.depends("room_ids")
    def _compute_qty_dining_room(self):
        type_id = self.env.ref(
            "pms_base.pms_room_type_dining", raise_if_not_found=False
        )
        for rec in self:
            rec.qty_dining_room = len(
                rec.room_ids.filtered(lambda x: x.type_id == type_id)
            )

    @api.depends("room_ids")
    def _compute_qty_kitchen(self):
        type_id = self.env.ref(
            "pms_base.pms_room_type_kitchen", raise_if_not_found=False
        )
        for rec in self:
            rec.qty_kitchen = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))

    @api.depends("room_ids")
    def _compute_qty_bedroom(self):
        type_id = self.env.ref("pms_base.pms_room_type_bed", raise_if_not_found=False)
        for rec in self:
            rec.qty_bedroom = len(rec.room_ids.filtered(lambda x: x.type_id == type_id))

    def action_view_childs_property_list(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pms_base.action_pms_property"
        )
        action["domain"] = [("id", "in", self.property_child_ids.ids)]
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.update({"is_property": True})
        return super().create(vals_list)

    def name_get(self):
        # Prefetch the fields used by the `name_get`,
        # so `browse` doesn't fetch other fields
        self.browse(self.ids).read(["name", "ref"])
        return [(property.id, "%s%s".format()) for property in self]

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("name", operator, name), ("ref", operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
