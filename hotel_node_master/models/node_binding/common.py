# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class NodeBinding(models.AbstractModel):
    _name = 'node.binding'
    _inherit = 'external.binding'
    _description = 'Hotel Node Connector Binding (abstract)'

    external_id = fields.Integer()
    backend_id = fields.Many2one(
        comodel_name='node.backend',
        string='Hotel Node Connector Backend',
        required=True,
        ondelete='restrict')

    _sql_constraints = [
        ('backend_external_id_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same Backend ID.'),
    ]
