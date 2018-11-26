# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class ChannelOtaInfoImporter(Component):
    _name = 'channel.ota.info.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.ota.info']
    _usage = 'ota.info.importer'

    @api.model
    def import_otas_info(self):
        raise NotImplementedError

    @api.model
    def push_activation(self, base_url):
        raise NotImplementedError
