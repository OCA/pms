# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import Component

class HotelConnectorModelBinder(Component):
    _name = 'hotel.channel.connector.binder'
    _inherit = ['base.binder', 'base.hotel.channel.connector']
    _apply_on = []
