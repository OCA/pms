# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent

class BaseHotelChannelConnectorComponent(AbstractComponent):
    _name = 'base.node.connector'
    _inherit = 'base.connector'
    _collection = 'node.backend'
