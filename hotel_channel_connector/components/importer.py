# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent

class HotelChannelConnectorImporter(AbstractComponent):
    _name = 'hotel.channel.importer'
    _inherit = ['base.importer', 'base.hotel.channel.connector']
    _usage = 'channel.importer'
