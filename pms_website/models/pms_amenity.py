# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsAmenity(models.Model):
    _inherit = "pms.amenity"

    is_main_amenity = fields.Boolean(
        string="Main Amenity", help="Main Amenity", default=False
    )
