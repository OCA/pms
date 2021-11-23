# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    property_ids = fields.Many2many(
        "pms.property",
        "pms_property_account_move_line_rel",
        "account_move_line_id",
        "property_id",
        string="Properties",
        readonly=True,
        copy=False,
    )
