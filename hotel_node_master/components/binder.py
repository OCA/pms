# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component

class NodeConnectorModelBinder(Component):
    _name = 'node.connector.binder'
    _inherit = ['base.binder', 'base.node.connector']
    _apply_on = [
        'node.room.type',
    ]
