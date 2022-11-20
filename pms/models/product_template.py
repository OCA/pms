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
        string="Daily limit",
        help="Indicates how much products can consumed in one day",
        compute="_compute_daily_limit",
        inverse="_inverse_daily_limit",
    )
    list_price = fields.Float(
        compute="_compute_list_price",
        inverse="_inverse_list_price",
    )
    is_extra_bed = fields.Boolean(
        string="Is extra bed",
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

    @api.depends_context("allowed_pms_property_ids")
    def _compute_daily_limit(self):
        for record in self:
            pms_property_id = (
                self.env.context.get("property")
                or self.env.user.get_active_property_ids()[0]
            )
            record.daily_limit = self.env["ir.pms.property"].get_field_value(
                pms_property_id,
                self._name,
                "daily_limit",
                record.id,
                type(record.daily_limit),
            )

    @api.depends_context("allowed_pms_property_ids")
    def _compute_list_price(self):
        for record in self:
            pms_property_id = (
                self.env.context.get("property")
                or self.env.user.get_active_property_ids()[0]
            )
            record.list_price = self.env["ir.pms.property"].get_field_value(
                pms_property_id,
                self._name,
                "list_price",
                record.id,
                type(record.list_price),
            )

    def _inverse_daily_limit(self):
        for record in self:
            pms_property_id = (
                self.env.context.get("property")
                or self.env.user.get_active_property_ids()[0]
            )
            self.env["ir.pms.property"].set_field_value(
                pms_property_id,
                self._name,
                "daily_limit",
                record.id,
                record.daily_limit,
            )

    def _inverse_list_price(self):
        for record in self:
            pms_property_id = (
                self.env.context.get("property")
                or self.env.user.get_active_property_ids()[0]
            )
            self.env["ir.pms.property"].set_field_value(
                pms_property_id, self._name, "list_price", record.id, record.list_price
            )
            # Set default value in other properties
            other_properties = self.env["pms.property"].search([])
            for other_property in other_properties.ids:
                if not self.env["ir.pms.property"].get_field_value(
                    other_property,
                    self._name,
                    "list_price",
                    record.id,
                    type(record.list_price),
                ):
                    self.env["ir.pms.property"].set_field_value(
                        other_property,
                        self._name,
                        "list_price",
                        record.id,
                        record.list_price,
                    )
