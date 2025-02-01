from odoo import fields, models


class PmsTeamMember(models.Model):
    _name = "pms.team.member"
    _description = "PMS Team Member"

    name = fields.Char(
        store=True,
        related="user_id.name",
    )
    active = fields.Boolean(
        default=True,
    )
    sequence = fields.Integer(
        default=10,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        comodel_name="pms.property",
        store=True,
        index=True,
        ondelete="restrict",
    )
    user_id = fields.Many2one(
        string="User Member",
        copy=False,
        comodel_name="res.users",
        ondelete="restrict",
        index=True,
    )
    pms_role = fields.Selection(
        help="The member role in the organization"
        "It can be 'Reception', 'Revenue', 'Administrative', or 'Manager'",
        copy=False,
        selection=[
            ("reception", "Reception"),
            ("revenue", "Revenue"),
            ("administrative", "Administrative"),
            ("manager", "Operational Manager"),
        ],
        required=True,
    )
