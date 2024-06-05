# Copyright (C) 2024 Irlui Ramírez <iramirez.spain@gmail.com>
# Copyright (C) 2024 Oso Tranquilo <informatica@gmail.com>
# Copyright (C) 2024 Consultores Hoteleros Integrales <www.aldahotels.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsHelpdeskTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    tag_ids = fields.Many2many(
        comodel_name="helpdesk.ticket.tag",
        relation="helpdesk_ticket_team_tag_rel",
        column1="team_id",
        column2="tag_id",
        string="Tags",
    )
