# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons.queue_job.job import job


class ChannelBinding(models.AbstractModel):
    _name = 'channel.binding'
    _inherit = 'external.binding'
    _description = 'Hotel Channel Connector Binding (abstract)'

    backend_id = fields.Many2one(
        comodel_name='channel.backend',
        string='Hotel Channel Connector Backend',
        required=True,
        ondelete='restrict')

    external_id = fields.Char(string='ID on Channel')

    _sql_constraints = [
        ('channel_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same Channel ID.'),
    ]

    @api.model
    def create_issue(self, **kwargs):
        self.env['hotel.channel.connector.issue'].sudo().create({
            'backend_id': kwargs.get('backend', self.backend_id.id),
            'section': kwargs.get('section', False),
            'internal_message': kwargs.get('internal_message', False),
            'channel_object_id': kwargs.get('channel_object_id', False),
            'channel_message': kwargs.get('channel_message', False),
            'date_start': kwargs.get('dfrom', False),
            'date_end': kwargs.get('dto', False),
        })
