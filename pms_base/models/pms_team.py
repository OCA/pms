# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PMSTeam(models.Model):
    _name = "pms.team"
    _description = "PMS Team"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_stages(self):
        return self.env["pms.stage"].search([("is_default", "=", True)])

    @api.depends("property_ids")
    def _compute_property_count(self):
        for rec in self:
            rec.property_count = len(rec.property_ids)

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    color = fields.Integer("Color Index")
    stage_ids = fields.Many2many(
        "pms.stage", string="Stages", default=lambda self: self._default_stages()
    )
    property_ids = fields.One2many("pms.property", "team_id", string="Properties")
    property_count = fields.Integer(
        compute="_compute_property_count", string="Properties Count"
    )
    sequence = fields.Integer(default=1, help="Used to sort teams. Lower is better.")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=False,
        index=True,
        default=lambda self: self.env.company.id,
        help="Company related to this team",
    )

    _sql_name_uniq = models.Constraint("unique (name)", "Team name already exists!")
