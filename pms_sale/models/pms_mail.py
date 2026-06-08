# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PMSMailScheduler(models.Model):
    _name = "pms.mail"
    _description = "PMS Automated Mailing"

    name = fields.Char(required=True)
    notification_type = fields.Selection(
        [("email", "Email")], string="Send", default="Email"
    )
    template_id = fields.Many2one("mail.template", string="Email Template")
    interval = fields.Integer(default=1)
    interval_unit = fields.Many2one(
        "uom.uom",
        string="Unit",
        domain=lambda self: [
            ("id", "child_of", self.env.ref("uom.product_uom_hour").id)
        ],
    )
    interval_trigger = fields.Selection(
        [
            ("after_resev", "After the reservation"),
            ("before_checkin", "Before Checkin"),
            ("after_checkin", "After Checkin"),
            ("before_checkout", "Before Checkout"),
            ("after_checkout", "After Checkout"),
        ],
        string="Trigger",
    )
    property_id = fields.Many2one("pms.property", string="Property")
