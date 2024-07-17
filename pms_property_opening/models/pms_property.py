# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    open_date = fields.Datetime(
        string="Open date", default=fields.Datetime.now, help="Property opening date."
    )
