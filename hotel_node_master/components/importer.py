# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import AbstractComponent, Component
_logger = logging.getLogger(__name__)

class NodeImporter(AbstractComponent):
    _name = 'node.importer'
    _inherit = ['base.importer', 'base.node.connector']
    _usage = 'node.importer'
