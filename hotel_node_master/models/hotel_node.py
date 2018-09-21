# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import wdb
import logging
import urllib.error
import odoorpc.odoo
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HotelNode(models.Model):

    _inherit = ['project.project']

    _description = 'Centralized hotel management features'

    active = fields.Boolean('Active', default=True,
                            help='The active field allows you to hide the \
                            node without removing it.')
    sequence = fields.Integer('Sequence', default=0,
                              help='Gives the sequence order when displaying the list of Nodes.')

    odoo_version = fields.Char()
    odoo_host = fields.Char('Host', required=True,
                            help='Full URL to the host.')
    odoo_db = fields.Char('Database Name',
                          help='Odoo database name.')
    odoo_user = fields.Char('Username',
                            help='Odoo administration user.')
    odoo_password = fields.Char('Password',
                                help='Odoo password.')
    odoo_port = fields.Integer(string='TCP Port', default=443,
                               help='Specify the TCP port for the XML-RPC protocol.')
    odoo_protocol = fields.Selection([('jsonrpc', 'jsonrpc'), ('jsonrpc+ssl', 'jsonrpc+ssl')],
                                     'Protocol', required=True, default='jsonrpc+ssl')

    user_ids = fields.One2many('hotel.node.user', 'node_id',
                               'Users with access to this hotel')

    group_ids = fields.Many2many('hotel.node.group', 'hotel_node_group_rel', 'node_id', 'group_id',
                                 string='Access Groups')

    room_type_ids = fields.One2many('hotel.node.room.type', 'node_id',
                                    'Rooms Type in this hotel')

    @api.constrains('group_ids')
    def _check_group_version(self):
        """
        :raise: ValidationError
        """
        for node in self:
            domain = [('id', 'in', node.group_ids.ids), ('odoo_version', '!=', node.odoo_version)]
            invalid_groups = self.env["hotel.node.group"].search(domain)
            if len(invalid_groups) > 0:
                msg = _("At least one group is not within the node version.") + " " + \
                      _("Odoo version of the node: %s") % node.odoo_version
                _logger.warning(msg)
                raise ValidationError(msg)

    _sql_constraints = [
        ('db_node_id_uniq', 'unique (odoo_db, id)',
         'The database name of the hotel must be unique within the Master Node!'),
    ]

    @api.model
    def create(self, vals):
        """
        :param dict vals: the model's fields as a dictionary
        :return: new hotel node record created.
        :raise: ValidationError
        """
        try:
            noderpc = odoorpc.ODOO(vals['odoo_host'], vals['odoo_protocol'], vals['odoo_port'])
            noderpc.login(vals['odoo_db'], vals['odoo_user'], vals['odoo_password'])

            vals.update({'odoo_version': noderpc.version})

            # Read remote Groups
            remote_domain = [('model', '=', 'res.groups')]
            remote_fields = ['complete_name', 'display_name']
            remote_groups = noderpc.env['ir.model.data'].search_read(remote_domain, remote_fields)

            # Read remote Room Types
            remote_fields = ['name', 'active', 'sequence']
            remote_room_types = noderpc.env['hotel.room.type'].search_read([], remote_fields)

            wdb.set_trace()

            noderpc.logout()

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            raise ValidationError(err)
        else:
            # Process Groups
            master_groups = self.env["hotel.node.group"].search_read(
                [('odoo_version', '=', vals['odoo_version'])], ['xml_id'])

            gui_ids = [r['id'] for r in master_groups]
            xml_ids = [r['xml_id'] for r in master_groups]

            group_ids = []
            for group in remote_groups:
                if group['complete_name'] in xml_ids:
                    idx = xml_ids.index(group['complete_name'])
                    group_ids.append((4, gui_ids[idx], 0))
                else:
                    group_ids.append((0, 0, {
                        'name': group['display_name'],
                        'xml_id': group['complete_name'],
                        'odoo_version': vals['odoo_version'],
                    }))
            vals.update({'group_ids': group_ids})

            # Process Room Type
            room_type_ids = []
            for room_type in remote_room_types:
                room_type_ids.append((0, 0, {
                    'name': room_type['name'],
                    'active': room_type['active'],
                    'sequence': room_type['sequence'],
                    'remote_room_type_id': room_type['id'],
                }))
            vals.update({'room_type_ids': room_type_ids})

            node_id = super().create(vals)

            return node_id
