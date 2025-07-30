# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsCancelationRule(models.Model):
    _name = "pms.cancelation.rule"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Cancelation Rules"
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Cancelation Rule",
        required=True,
        tracking=True,
        translate=True,
    )
    pms_property_ids = fields.Many2many(
        comodel_name="pms.property",
        relation="pms_cancelation_rule_pms_property_rel",
        column1="pms_cancelation_rule_id",
        column2="pms_property_id",
        string="Properties",
        ondelete="restrict",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        check_pms_properties=True,
    )
    active = fields.Boolean(
        help="Determines if cancelation rule is active", default=True
    )
    days_intime = fields.Integer(
        string="Free Cancellation",
        tracking=True,
        help="Maximum number of days for free cancellation before Checkin",
    )
    penalty_late = fields.Integer(
        string="Penalty Late (%)",
        default="100",
        tracking=True,
        help="Percentage of the total price that partner has "
        "to pay in case of late arrival",
    )
    apply_on_late = fields.Selection(
        selection=[
            ("first", "First Day"),
            ("all", "All Days"),
            ("days", "Specify days"),
        ],
        default="first",
        string="Late apply on",
        tracking=True,
        help="Days on which the cancelation rule applies when "
        "the reason is late arrival. "
        "Can be first, all days or specify the days.",
    )
    days_late = fields.Integer(
        string="Late first days",
        default="2",
        tracking=True,
        help="Is number of days late in the cancelation rule "
        "if the value of the apply_on_late field is specify days.",
    )
    penalty_noshow = fields.Integer(
        string="Penalty No Show (%)",
        default="100",
        tracking=True,
        help="Percentage of the total price that partner has to pay in case of no show",
    )
    apply_on_noshow = fields.Selection(
        selection=[
            ("first", "First Day"),
            ("all", "All Days"),
            ("days", "Specify days"),
        ],
        default="all",
        string="No Show apply on",
        tracking=True,
        help="Days on which the cancelation rule applies when"
        " the reason is no show. Can be first, all days or specify the days.",
    )
    days_noshow = fields.Integer(
        string="NoShow first days",
        default="2",
        tracking=True,
        help="Is number of days no show in the cancelation rule "
        "if the value of the apply_on_show field is specify days.",
    )
