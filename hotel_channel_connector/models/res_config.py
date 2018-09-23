# Copyright 2018  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class HotelConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    default_channel_connector = fields.Many2one(
        'channel.backend',
        'Default Channel Connector Backend')

    @api.multi
    def set_values(self):
        super(HotelConfiguration, self).set_values()

        self.env['ir.default'].sudo().set(
            'res.config.settings', 'default_channel_connector',
            self.default_channel_connector.id)

    @api.model
    def get_values(self):
        res = super(HotelConfiguration, self).get_values()

        # ONLY FOR v11. DO NOT FORWARD-PORT
        default_channel_connector = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_channel_connector')

        res.update(
            default_channel_connector=default_channel_connector,
        )
        return res
