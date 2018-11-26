# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo import api


class BaseHotelChannelConnectorComponent(AbstractComponent):
    _name = 'base.hotel.channel.connector'
    _inherit = 'base.connector'
    _collection = 'channel.backend'

    @api.model
    def create_issue(self, **kwargs):
        self.env['hotel.channel.connector.issue'].sudo().create({
            'backend_id': kwargs.get('backend', self.backend_record.id),
            'section': kwargs.get('section', False),
            'internal_message': kwargs.get('internal_message', False),
            'channel_object_id': kwargs.get('channel_object_id', False),
            'channel_message': kwargs.get('channel_message', False),
            'date_start': kwargs.get('dfrom', False),
            'date_end': kwargs.get('dto', False),
        })

class ChannelConnectorError(Exception):
    def __init__(self, message, data):
        super().__init__(message)
        self.data = data
