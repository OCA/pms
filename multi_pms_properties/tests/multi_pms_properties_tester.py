# Copyright 2021 Eric Antones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ParentTester(models.Model):
    _name = "pms.parent.tester"

    name = fields.Char(required=True)


class ChildTester(models.Model):
    _name = "pms.child.tester"

    name = fields.Char(required=True)
    parent_id = fields.Many2one("pms.parent.tester", check_pms_properties=True)
