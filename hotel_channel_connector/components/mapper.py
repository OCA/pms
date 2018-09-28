# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelImportMapper(AbstractComponent):
    _name = 'channel.import.mapper'
    _inherit = ['base.hotel.channel.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class ChannelExportMapper(AbstractComponent):
    _name = 'channel.export.mapper'
    _inherit = ['base.hotel.channel.connector', 'base.export.mapper']
    _usage = 'export.mapper'
