# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


#  TODO: refactoring to cancellation.rule
class PmsCancelationRule(models.Model):
    _name = "pms.cancelation.rule"
    _description = "Cancelation Rules"

    # Fields declaration
    name = fields.Char("Amenity Name", translate=True, required=True)
    pricelist_ids = fields.One2many(
        "product.pricelist", "cancelation_rule_id", "Pricelist that use this rule"
    )
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    active = fields.Boolean("Active", default=True)
    days_intime = fields.Integer(
        "Days Late", help="Maximum number of days for free cancellation before Checkin"
    )
    penalty_late = fields.Integer("% Penalty Late", default="100")
    apply_on_late = fields.Selection(
        [("first", "First Day"), ("all", "All Days"), ("days", "Specify days")],
        "Late apply on",
        default="first",
    )
    days_late = fields.Integer("Late first days", default="2")
    penalty_noshow = fields.Integer("% Penalty No Show", default="100")
    apply_on_noshow = fields.Selection(
        [("first", "First Day"), ("all", "All Days"), ("days", "Specify days")],
        "No Show apply on",
        default="all",
    )
    days_noshow = fields.Integer("NoShow first days", default="2")

    # TODO: Constrain coherence pms_property_ids pricelist and cancelation_rules
