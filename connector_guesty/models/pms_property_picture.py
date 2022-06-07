# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsPropertyPicture(models.Model):
    _name = "pms.property.picture"
    _description = "Property Pictures"

    name = fields.Char(required=1)
    property_id = fields.Many2one("pms.property")

    url_small = fields.Char()
    url_medium = fields.Char()
    url_large = fields.Char()
    url_thumbnail = fields.Char()

    original_data = fields.Binary(string="Picture Data")

    external_id = fields.Char()
