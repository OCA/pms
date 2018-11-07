# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HotelNodeGroup(models.Model):
    _name = "hotel.node.group"
    _description = "Hotel Access Groups"

    active = fields.Boolean(default=True,
                            help="The active field allows you to hide the \
                            group without removing it.")
    sequence = fields.Integer(default=0,
                              help="Gives the sequence order when displaying the list of Groups.")

    name = fields.Char(required=True, translate=True)
    # node_ids = fields.Many2many('project.project', 'hotel_node_group_rel', 'group_id', 'node_id',
    #                             string='Hotels')
    remote_group_ids = fields.One2many('hotel.node.group.remote', 'group_id',
                                'Access Groups')
    user_ids = fields.Many2many('hotel.node.user', 'hotel_node_user_group_rel', 'group_id', 'user_id',
                                string='Users')
    # xml_id represents the complete module.name, xml_id = ("%s.%s" % (data['module'], data['name']))
    xml_id = fields.Char(string='External Identifier', required=True,
                         help="External Key/Identifier that can be used for "
                              "data integration with third-party systems")
    odoo_version = fields.Char('Odoo Version')

    _sql_constraints = [
        ('xml_id_uniq', 'unique (odoo_version, xml_id)',
         'The external identifier of the group must be unique within an Odoo version!')
    ]

