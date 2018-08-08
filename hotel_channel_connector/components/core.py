from odoo.addons.component.core import AbstractComponent


class BaseHotelChannelConnectorComponent(AbstractComponent):
    _name = 'base.hotel.channel.connector'
    _inherit = 'base.connector'
    _collection = 'hotel.channel.backend'

    @api.model
    def create_issue(self, section, message, wmessage, wid=False,
                     dfrom=False, dto=False):
        self.env['hotel.channel.connector.issue'].sudo().create({
            'section': section,
            'message': message,
            'wid': wid,
            'wmessage': wmessage,
            'date_start': dfrom and dfrom.strftime(DEFAULT_SERVER_DATE_FORMAT),
            'date_end': dto and dto.strftime(DEFAULT_SERVER_DATE_FORMAT),
        })
