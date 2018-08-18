# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action


class ChannelBinding(models.AbstractModel):
    _name = 'channel.binding'
    _inherit = 'external.binding'
    _description = 'Hotel Channel Connector Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='channel.backend',
        string='Hotel Channel Connector Backend',
        required=True,
        ondelete='restrict')
