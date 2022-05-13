# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsGuestyCustomField(models.Model):
    _name = "pms.guesty.custom_field"

    name = fields.Char(string="Name", required=True)
    external_id = fields.Char(string="External ID", required=True)
    custom_field_id = fields.Char(required=True)

    _sql_constraints = [
        ("external_id_uniq", "unique (external_id)", "Field ID already exists!")
    ]


class PmsGuestyCustomFieldBackend(models.Model):
    _name = "pms.backend.custom_field"

    name = fields.Selection(
        [
            ("company", "Company"),
            ("keycode", "Keycode"),
        ]
    )

    guesty_custom_field_id = fields.Many2one(
        "pms.guesty.custom_field", string="Guesty Field", required=True
    )
    backend_id = fields.Many2one("backend.guesty", string="Backend", required=True)
