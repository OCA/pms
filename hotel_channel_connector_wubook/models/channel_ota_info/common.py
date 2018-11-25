# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.component.core import Component


class ChannelOtaInfo(models.Model):
    _inherit = 'channel.ota.info'

    ical = fields.Boolean("ical", default=False)


class HotelRoomTypeAdapter(Component):
    _name = 'channel.ota.info.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.ota.info'

    def fetch_rooms(self):
        return super(HotelRoomTypeAdapter, self).fetch_rooms()

    def push_activation(self, base_url, security_token):
        return super(HotelRoomTypeAdapter, self).push_activation(base_url, security_token)
