# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo import api

class BaseHotelChannelConnectorComponent(AbstractComponent):
    _name = 'base.hotel.channel.connector'
    _inherit = 'base.connector'
    _collection = 'channel.backend'

class ChannelConnectorError(Exception):
    def __init__(self, message, data):
        super().__init__(message)
        self.data = data
