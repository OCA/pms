# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

class NodeExporter(AbstractComponent):
    _name = 'node.exporter'
    _inherit = ['base.exporter', 'base.node.connector']
    _usage = 'node.exporter'
