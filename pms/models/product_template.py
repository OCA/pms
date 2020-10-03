# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    per_day = fields.Boolean("Unit increment per day")
    per_person = fields.Boolean("Unit increment per person")
    consumed_on = fields.Selection(
        [("before", "Before night"), ("after", "After night")],
        "Consumed",
        default="before",
    )
    daily_limit = fields.Integer("Daily limit")
    is_extra_bed = fields.Boolean("Is extra bed", default=False)
    show_in_calendar = fields.Boolean(
        "Show in Calendar",
        default=False,
        help="Specifies if the product is shown in the calendar information.",
    )
