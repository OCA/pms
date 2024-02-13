from odoo import fields, models


class PmsHousekeepingCancellationType(models.Model):
    _name = "pms.housekeeping.cancellation.type"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
