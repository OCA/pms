# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    property_id = fields.Many2one(
        "pms.property",
        string="Property",
    )
