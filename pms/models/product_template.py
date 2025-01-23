# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="product_template_pms_property_rel",
        column1="product_tmpl_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    per_day = fields.Boolean(
        string="Unit increment per day",
        help="Indicates that the product is sold by days",
    )
    per_person = fields.Boolean(
        string="Unit increment per person",
        help="Indicates that the product is sold per person",
    )
    consumed_on = fields.Selection(
        string="Consumed",
        help="Indicates when the product is consumed",
        selection=[("before", "Before night"), ("after", "After night")],
        default="before",
    )
    daily_limit = fields.Integer(
        help="Indicates how much products can consumed in one day",
        compute="_compute_daily_limit",
        inverse="_inverse_daily_limit",
    )
    is_extra_bed = fields.Boolean(
        help="Indicates if that product is a extra bed, add +1 capacity in the room",
        default=False,
    )
    is_crib = fields.Boolean(
        string="Is a baby crib",
        help="Indicates if that product is a crib",
        default=False,
    )
    is_pms_available = fields.Boolean(
        string="Is available in PMS",
        help="Indicates if that product is available in PMS",
        default=True,
    )
    is_tourist_tax = fields.Boolean(
        string="Is tourist tax",
        help="Indicates if that product is a tourist tax",
        default=False,
    )
    touristic_calculation = fields.Selection(
        string="Touristic calculation",
        help="Indicates how the tourist tax is calculated",
        selection=[
            ("occupany", "Occupancy"),
            ("nights", "Nights"),
            ("occupancyandnights", "Occupancy and Nights"),
        ],
        default="occupancyandnights",
    )
    occupancy_domain = fields.Char(
        string="Occupancy domain",
        help="Domain to filter checkins",
        default="",
    )
    nights_domain = fields.Char(
        string="Nights domain",
        help="Domain to filter reservations",
        default="[('state', '!=', 'cancel')]",
    )
    property_daily_limits = fields.One2many(
        string="Daily Limits per Property",
        comodel_name="ir.pms.property",
        inverse_name="record",
        domain=lambda self: [
            ("model_id.model", "=", "product.template"),
            ("field_id.name", "=", "daily_limit"),
        ],
    )

    @api.depends_context("allowed_pms_property_ids")
    def _compute_daily_limit(self):
        for record in self:
            pms_property_id = self.env.context.get("property")
            record.daily_limit = self.env["ir.pms.property"].get_field_value(
                pms_property_id,
                self._name,
                "daily_limit",
                record.id,
                type(record.daily_limit),
            )

    def _inverse_daily_limit(self):
        for record in self:
            pms_property_id = self.env.context.get("property")
            self.env["ir.pms.property"].set_field_value(
                pms_property_id,
                self._name,
                "daily_limit",
                record.id,
                record.daily_limit,
            )
