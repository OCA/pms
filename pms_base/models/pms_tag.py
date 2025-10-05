# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2021 Eric Antones <eantones@nuobit.com>
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsTag(models.Model):
    _name = "pms.tag"
    _description = "PMS Tag"

    name = fields.Char(required=True, translate=True)
    parent_id = fields.Many2one("pms.tag")
    color = fields.Integer("Color Index", default=10)
    full_name = fields.Char(compute="_compute_full_name")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company.id,
        help="Company related to this tag",
    )

    _sql_constraints = [
        ("name_uniq", "unique (name, company_id)", "Tag name already exists!")
    ]

    def _compute_full_name(self):
        for record in self:
            if record.parent_id:
                record.full_name = record.parent_id.name + "/" + record.name
            else:
                record.full_name = record.name
