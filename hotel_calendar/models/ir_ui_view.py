# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields

class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('pms', "PMS"), ('mpms', 'Management PMS')])
