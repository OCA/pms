# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


#  TODO: refactoring to cancellation.rule
class PmsCancelationRule(models.Model):
    _name = "pms.cancelation.rule"
    _description = "Cancelation Rules"
    _check_pms_properties_auto = True

    # Fields declaration
    name = fields.Char(string="Cancelation Rule", translate=True, required=True)
    pricelist_ids = fields.One2many(
        "product.pricelist",
        "cancelation_rule_id",
        "Pricelist that use this rule",
        check_pms_properties=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        ondelete="restrict",
        comodel_name="pms.property",
        relation="pms_cancelation_rule_pms_property_rel",
        column1="pms_cancelation_rule_id",
        column2="pms_property_id",
        check_pms_properties=True,
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
