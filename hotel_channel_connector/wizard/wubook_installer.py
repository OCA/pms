# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import binascii
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from ..wubook import DEFAULT_WUBOOK_DATE_FORMAT
from odoo.addons.hotel import date_utils


class WuBookInstaller(models.TransientModel):
    _name = 'wubook.installer'
    _inherit = 'res.config.installer'

    wubook_user = fields.Char('User', required=True)
    wubook_passwd = fields.Char('Password', required=True)
    wubook_lcode = fields.Char('LCode', required=True)
    wubook_server = fields.Char(string='Server',
                                default='https://wired.wubook.net/xrws/',
                                required=True)
    wubook_pkey = fields.Char('PKey', required=True)
    activate_push = fields.Boolean('Active Push Notifications', default=True)

    @api.multi
    def execute(self):
        super(WuBookInstaller, self).execute()
        return self.execute_simple()

    @api.multi
    def execute_simple(self):
        activate_push = True
        for rec in self:
            self.env['ir.default'].sudo().set('wubook.config.settings',
                                                     'wubook_user',
                                                     rec.wubook_user)
            self.env['ir.default'].sudo().set('wubook.config.settings',
                                                     'wubook_passwd',
                                                     rec.wubook_passwd)
            self.env['ir.default'].sudo().set('wubook.config.settings',
                                                     'wubook_lcode',
                                                     rec.wubook_lcode)
            self.env['ir.default'].sudo().set('wubook.config.settings',
                                                     'wubook_server',
                                                     rec.wubook_server)
            self.env['ir.default'].sudo().set('wubook.config.settings',
                                                     'wubook_pkey',
                                                     rec.wubook_pkey)
            activate_push = rec.activate_push
        self.env['ir.default'].sudo().set(
            'wubook.config.settings',
            'wubook_push_security_token',
            binascii.hexlify(os.urandom(16)).decode())
        self.env.cr.commit()    # FIXME: Need do this

        # Create Wubook Base Restrictions
        restr_obj = self.env['hotel.virtual.room.restriction'].with_context({
            'wubook_action': False
        })
        base_rest = restr_obj.search([('wpid', '=', '0')], limit=1)
        if not base_rest:
            nrest = restr_obj.create({
                'name': 'Base WuBook Restrictions',
                'wpid': '0',
            })
            if not nrest:
                raise ValidationError(_("Can't create base wubook restrictions"))

        # Initialize WuBook
        wres = self.env['wubook'].initialize(activate_push)
        if not wres:
            raise ValidationError("Can't finish installation!")

        # Open Next Step
        v_id = 'hotel_wubook_proto.view_wubook_configuration_installer_parity'
        return {
            'name': _("Configure Hotel Parity"),
            'type': 'ir.actions.act_window',
            'res_model': 'wubook.installer.parity',
            'view_id': self.env.ref(v_id).id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }


class WuBookInstallerParity(models.TransientModel):
    _name = 'wubook.installer.parity'
    _inherit = 'res.config.installer'

    parity_pricelist_id = fields.Many2one('product.pricelist',
                                          'Product Pricelist')
    parity_restrictions_id = fields.Many2one('hotel.virtual.room.restriction',
                                             'Restrictions')
    import_data = fields.Boolean('Import Data From WuBook', default=False)
    date_start = fields.Date('Date Start')
    date_end = fields.Date('Date End')

    @api.multi
    def execute(self):
        self.execute_simple()
        return super(WuBookInstallerParity, self).execute()

    @api.multi
    def execute_simple(self):
        wubookObj = self.env['wubook']
        irValuesObj = self.env['ir.values']
        for rec in self:
            irValuesObj.sudo().set_default('hotel.config.settings',
                                           'parity_pricelist_id',
                                           rec.parity_pricelist_id.id)
            irValuesObj.sudo().set_default('hotel.config.settings',
                                           'parity_restrictions_id',
                                           rec.parity_restrictions_id.id)
            import_data = rec.import_data
            if rec.import_data:
                date_start_dt = date_utils.get_datetime(rec.date_start)
                date_end_dt = date_utils.get_datetime(rec.date_end)
                # Availability
                wresAvail = wubookObj.fetch_rooms_values(
                    date_start_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    date_end_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))
                # Pricelist
                wresPrices = wubookObj.fetch_plan_prices(
                    rec.parity_pricelist_id.wpid,
                    date_start_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    date_end_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))
                # Restrictions
                wresRestr = wubookObj.fetch_rplan_restrictions(
                    date_start_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    date_end_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    rec.parity_restrictions_id.wpid)

                if not wresAvail or not wresPrices or not wresRestr:
                    raise ValidationError(_("Errors importing data from WuBook"))

                # Reservations
                wubookObj.fetch_new_bookings()
