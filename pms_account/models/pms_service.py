# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsService(models.Model):
    _inherit = "pms.service"

    vendor_id = fields.Many2one(
        string="Vendor",
        required=True,
        comodel_name="res.partner",
        ondelete="restrict",
        domain="[('supplier_rank', '>=', 0)]",
    )
