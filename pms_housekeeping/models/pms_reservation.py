# Copyright 2021 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsRoom(models.Model):
    _inherit = "pms.reservation"

    dont_disturb = fields.Boolean(
        string="Dont disturb",
        default=False,
    )
