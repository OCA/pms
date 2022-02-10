# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PMSStage(models.Model):
    _name = "pms.stage"
    _description = "PMS Stage"
    _order = "sequence, name, id"

    def _default_team_ids(self):
        default_team_id = self.env.context.get("default_team_id")
        return [default_team_id] if default_team_id else None

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer("Sequence", default=1)
    fold = fields.Boolean(
        "Folded in Kanban",
        help="This stage is folded in the kanban view when "
        "there are no record in that stage to display.",
    )
    is_closed = fields.Boolean(
        "Is a close stage", help="Services in this stage are considered " "as closed."
    )
    is_default = fields.Boolean("Is a default stage", help="Used as default stage")
    description = fields.Text(translate=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=False,
        index=True,
        default=lambda self: self.env.company.id,
    )
    team_ids = fields.Many2many(
        "pms.team", string="Teams", default=lambda self: self._default_team_ids()
    )
    stage_type = fields.Selection([("property", "Property")], "Type", required=True)
    custom_color = fields.Char(
        "Color Code", default="#FFFFFF", help="Use Hex Code only Ex:-#FFFFFF"
    )
    active = fields.Boolean(string="Active", default=True)

    @api.constrains("custom_color")
    def _check_custom_color_hex_code(self):
        if (
            self.custom_color
            and not self.custom_color.startswith("#")
            or len(self.custom_color) != 7
        ):
            raise ValidationError(_("Color code should be Hex Code. Ex:-#FFFFFF"))
