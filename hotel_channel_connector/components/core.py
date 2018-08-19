from odoo.addons.component.core import AbstractComponent
from odoo import api

class BaseHotelChannelConnectorComponent(AbstractComponent):
    _name = 'base.hotel.channel.connector'
    _inherit = 'base.connector'
    _collection = 'hotel.channel.backend'

    @api.model
    def create_issue(self, section, message, channel_message, channel_object_id=False,
                     dfrom=False, dto=False):
        self.env['hotel.channel.connector.issue'].sudo().create({
            'section': section,
            'message': message,
            'channel_object_id': channel_object_id,
            'channel_message': channel_message,
            'date_start': dfrom,
            'date_end': dto,
        })
