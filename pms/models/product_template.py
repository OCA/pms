# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date

import babel

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
        check_pms_properties=True,
        ondelete="restrict",
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
        selection=[
            ("before", "All before night"),
            ("after", "All after night"),
            ("checkin", "Only first day"),
            ("checkout", "Only last day"),
        ],
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
    tourist_tax_date_start = fields.Selection(
        selection=lambda self: self._get_mmdd_selection(),
        string="Start Date (Annual)",
        required=False,
    )
    tourist_tax_date_end = fields.Selection(
        selection=lambda self: self._get_mmdd_selection(),
        string="End Date (Annual)",
        required=False,
    )
    tourist_tax_apply_from_night = fields.Integer(
        string="Apply From Night",
        default=1,
        help="Night number the rule starts applying (e.g., 1 = first night)",
    )
    tourist_tax_apply_to_night = fields.Integer(
        string="Apply Until Night",
        help="Night number the rule stops applying (optional)",
    )
    tourist_tax_min_age = fields.Integer(
        string="Minimum Age", help="Applies only to guests with this age or older"
    )
    tourist_tax_max_age = fields.Integer(
        string="Maximum Age", help="Applies only to guests up to this age"
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

    def write(self, vals):
        if vals.get("is_tourist_tax") is True:
            vals["is_pms_available"] = True
            vals["per_day"] = True
            vals["consumed_on"] = "before"
        return super().write(vals)

    def _get_mmdd_selection(self):
        lang = self.env.lang or "en_US"
        days_by_month = {
            1: 31,
            2: 29,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31,
        }

        options = []
        for month in range(1, 13):
            for day in range(1, days_by_month[month] + 1):
                mmdd = f"{month:02d}-{day:02d}"
                dt = date(2024, month, day)  # Dummy year
                label = babel.dates.format_date(dt, format="d MMMM", locale=lang)
                options.append((mmdd, label.capitalize()))
                # Capitalize first letter for consistency
        return options
