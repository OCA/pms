# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class HotelChannelConnectorDeleter(AbstractComponent):
    _name = 'hotel.channel.deleter'
    _inherit = ['base.deleter', 'base.hotel.channel.connector']
    _usage = 'channel.deleter'
