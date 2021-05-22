# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsCancelationRule(models.Model):
    _name = "pms.cancelation.rule"
    _description = "Cancelation Rules"
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Cancelation Rule",
        required=True,
        translate=True,
    )
    pricelist_ids = fields.One2many(
        string="Pricelist",
        help="Pricelist that use this rule",
        comodel_name="product.pricelist",
        inverse_name="cancelation_rule_id",
        check_pms_properties=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="pms_cancelation_rule_pms_property_rel",
        column1="pms_cancelation_rule_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    active = fields.Boolean(
        string="Active", help="Determines if cancelation rule is active", default=True
    )
    days_intime = fields.Integer(
        string="Days Late",
        help="Maximum number of days for free cancellation before Checkin",
    )
    penalty_late = fields.Integer(
        string="% Penalty Late",
        help="Percentage of the total price that partner has "
        "to pay in case of late arrival",
        default="100",
    )
    apply_on_late = fields.Selection(
        string="Late apply on",
        help="Days on which the cancelation rule applies when "
        "the reason is late arrival. "
        "Can be first, all days or specify the days.",
        default="first",
        selection=[
            ("first", "First Day"),
            ("all", "All Days"),
            ("days", "Specify days"),
        ],
    )
    days_late = fields.Integer(
        string="Late first days",
        help="Is number of days late in the cancelation rule "
        "if the value of the apply_on_late field is specify days.",
        default="2",
    )
    penalty_noshow = fields.Integer(
        string="% Penalty No Show",
        help="Percentage of the total price that partner has to pay in case of no show",
        default="100",
    )
    apply_on_noshow = fields.Selection(
        string="No Show apply on",
        help="Days on which the cancelation rule applies when"
        " the reason is no show. Can be first, all days or specify the days.",
        selection=[
            ("first", "First Day"),
            ("all", "All Days"),
            ("days", "Specify days"),
        ],
        default="all",
    )
    days_noshow = fields.Integer(
        string="NoShow first days",
        help="Is number of days no show in the cancelation rule "
        "if the value of the apply_on_show field is specify days.",
        default="2",
    )
