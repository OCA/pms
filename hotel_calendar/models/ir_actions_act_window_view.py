# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    # Fields declaration
    view_mode = fields.Selection(selection_add=[('pms', "PMS"), ('mpms', 'Management PMS')])
