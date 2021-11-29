# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PMSMailScheduler(models.Model):
    _name = "pms.mail"
    _description = "PMS Automated Mailing"

    name = fields.Char(string="Name", required=True)
    notification_type = fields.Selection(
        [("email", "Email")], string="Send", default="Email"
    )
    template_id = fields.Many2one("mail.template", string="Email Template")
    interval = fields.Integer("Interval", default=1)
    interval_unit = fields.Many2one(
        "uom.uom",
        string="Unit",
        domain=lambda self: [
            ("category_id", "=", self.env.ref("uom.uom_categ_wtime").id)
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
