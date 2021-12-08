# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartnerGuesty(models.Model):
    _name = "res.partner.guesty"
    _description = "Guesty Partner"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    guesty_id = fields.Char(required=True)
