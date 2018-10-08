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


class HotelNodeUser(models.Model):
    _name = "hotel.node.user"
    _description = "Users with access to a hotel"

    def _default_groups(self):
        pass

    active = fields.Boolean(default=True,
                            help="The active field allows you to hide the \
                            user without removing it.")
    sequence = fields.Integer(default=0,
                              help="Gives the sequence order when displaying the list of Users.")

    node_id = fields.Many2one('project.project', 'Hotel', required=True)
    # remote users are managed as partners into the central node
    partner_id = fields.Many2one('res.partner', required=True)
    name = fields.Char(related='partner_id.name')
    email = fields.Char(related='partner_id.email', readonly=True)

    login = fields.Char(related='partner_id.email', require=True,
                        help="Used to log into the hotel")
    password = fields.Char(default='', invisible=True, copy=False,
                           help="Keep empty if you don't want the user to be able to connect on the hotel.")
    remote_user_id = fields.Integer(require=True, invisible=True, copy=False, readonly=True,
                                    help="ID of the target record in the remote database")

    group_ids = fields.Many2many('hotel.node.group', 'hotel_node_user_group_rel', 'user_id', 'group_id',
                                 string='Groups', default=_default_groups, require=True,
                                 help="Access rights for this user in this hotel.")

    # Constraints and onchanges
    @api.constrains('group_ids')
    def _check_group_ids(self):
        # TODO ensure all group_ids are within the node version
        domain = [('id', 'in', self.group_ids.ids), ('odoo_version', '!=', self.node_id.odoo_version)]
        invalid_groups = self.env["hotel.node.group"].search_count(domain)
        if invalid_groups > 0:
            msg = _("At least one group is not within the node version.") + " " + \
                  _("Odoo version of the node: %s") % self.node_id.odoo_version
            _logger.warning(msg)
            raise ValidationError(msg)

    @api.onchange('node_id')
    def _onchange_node_id(self):
        if self.node_id:
            # TODO clean group_ids
            # self.group_ids = []
            return {'domain': {'group_ids': [('odoo_version', '=', self.node_id.odoo_version)]}}

        return {'domain': {'group_ids': []}}

    @api.model
    def create(self, vals):
        """
        :param dict vals: the model's fields as a dictionary
        :return: new hotel user record created.
        :raise: ValidationError
        """
        node = self.env["project.project"].browse(vals['node_id'])

        if 'group_ids' in vals:
            domain = [('id', 'in', vals['group_ids'][0][2]), ('odoo_version', '!=', node.odoo_version)]
            invalid_groups = self.env["hotel.node.group"].search_count(domain)
            if invalid_groups > 0:
                msg = _("At least one group is not within the node version.") + " " + \
                      _("Odoo version in node: %s") % node.odoo_version
                _logger.error(msg)
                raise ValidationError(msg)

        try:
            if 'is_synchronizing' not in self._context:
                noderpc = odoorpc.ODOO(node.odoo_host, node.odoo_protocol, node.odoo_port)
                noderpc.login(node.odoo_db, node.odoo_user, node.odoo_password)

                partner = self.env["res.partner"].browse(vals['partner_id'])
                remote_vals = {
                    'name': partner.name,
                    'login': vals['login'],
                }

                if 'group_ids' in vals:
                    groups = self.env["hotel.node.group"].browse(vals['group_ids'][0][2])
                    # TODO Improve one rpc call per remote group for better performance
                    remote_groups = [noderpc.env.ref(r.xml_id).id for r in groups]
                    remote_vals.update({'groups_id': [[6, False, remote_groups]]})

                # create user and delegate in remote node the default values for the user
                remote_user_id = noderpc.env['res.users'].create(remote_vals)
                _logger.info('User #%s created remote res.users with ID: [%s]',
                             self._context.get('uid'), remote_user_id)
                vals.update({'remote_user_id': remote_user_id})

                noderpc.logout()

        except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
            _logger.error(err)
            raise ValidationError(err)
        else:
            return super().create(vals)

    @api.multi
    def write(self, vals):
        """
        :param dict vals: a dictionary of fields to update and the value to set on them.
        :raise: ValidationError
        """
        for rec in self:
            if 'node_id' in vals and vals['node_id'] != rec.node_id.id:
                msg = _("Changing a user between nodes is not allowed. Please create a new user instead.")
                _logger.error(msg)
                raise ValidationError(msg)

            node = rec.node_id

            if 'group_ids' in vals:
                domain = [('id', 'in', vals['group_ids'][0][2]), ('odoo_version', '!=', node.odoo_version)]
                invalid_groups = self.env["hotel.node.group"].search_count(domain)
                if invalid_groups > 0:
                    msg = _("At least one group is not within the node version.") + " " + \
                          _("Odoo version in node: %s") % node.odoo_version
                    _logger.error(msg)
                    raise ValidationError(msg)

            try:
                if 'is_synchronizing' not in self._context:
                    noderpc = odoorpc.ODOO(node.odoo_host, node.odoo_protocol, node.odoo_port)
                    noderpc.login(node.odoo_db, node.odoo_user, node.odoo_password)

                    remote_vals = {}

                    if 'active' in vals:
                        remote_vals.update({'active': vals['active']})

                    if 'password' in vals:
                        remote_vals.update({'password': vals['password']})

                    if 'partner_id' in vals:
                        partner = self.env["res.partner"].browse(vals['partner_id'])
                        remote_vals.update({'name': partner.name})

                    if 'group_ids' in vals:
                        groups = self.env["hotel.node.group"].browse(vals['group_ids'][0][2])
                        # TODO Improve one rpc call per remote group for better performance
                        remote_groups = [noderpc.env.ref(r.xml_id).id for r in groups]
                        remote_vals.update({'groups_id': [[6, False, remote_groups]]})

                    noderpc.env['res.users'].write([rec.remote_user_id], remote_vals)
                    _logger.info('User #%s updated remote res.users with ID: [%s]',
                                 self._context.get('uid'), rec.remote_user_id)

                    noderpc.logout()

            except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
                _logger.error(err)
                raise ValidationError(err)

        # TODO update record in central node only if the corresponding remote call was successfully
        return super().write(vals)

    @api.multi
    def unlink(self):
        """
        :raise: ValidationError
        """
        for rec in self:
            try:
                node = rec.node_id

                noderpc = odoorpc.ODOO(node.odoo_host, node.odoo_protocol, node.odoo_port)
                noderpc.login(node.odoo_db, node.odoo_user, node.odoo_password)
                # TODO In production users are archived instead of removed
                # noderpc.env['res.users'].unlink([rec.remote_user_id])
                noderpc.env['res.users'].write([rec.remote_user_id], {'active': False})
                _logger.info('User #%s deleted remote res.users with ID: [%s]',
                             self._context.get('uid'), rec.remote_user_id)
                noderpc.logout()

                # TODO How to manage the relationship with the partner? Also deleted?

            except (odoorpc.error.RPCError, odoorpc.error.InternalError, urllib.error.URLError) as err:
                _logger.error(err)
                raise ValidationError(err)

        return super().unlink()
