# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class NodeImportMapper(AbstractComponent):
    _name = 'node.import.mapper'
    _inherit = ['base.node.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class NodeExportMapper(AbstractComponent):
    _name = 'node.export.mapper'
    _inherit = ['base.node.connector', 'base.export.mapper']
    _usage = 'export.mapper'
