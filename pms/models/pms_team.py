from odoo import fields, models


class PmsTeam(models.Model):
    _name = "pms.team"
    _inherit = ["mail.thread"]
    _description = "PMS Team"
    _check_pms_properties_auto = True

    name = fields.Char("PMS Team", required=True)
    sequence = fields.Integer("Sequence", default=10)
    active = fields.Boolean(default=True)
    pms_property_id = fields.Many2one("pms.property", string="Property")
    user_id = fields.Many2one("res.users", string="Team Leader")
    member_ids = fields.One2many("res.users", "pms_team_id", string="Channel Members")
