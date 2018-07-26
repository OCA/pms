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
from datetime import timedelta
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.hotel import date_utils
from ..wubook import DEFAULT_WUBOOK_DATE_FORMAT


class VirtualRoomAvailability(models.Model):
    _inherit = 'hotel.virtual.room.availability'

    @api.model
    def _default_wmax_avail(self):
        if self.virtual_room_id:
            return self.virtual_room_id.max_real_rooms
        return -1

    wmax_avail = fields.Integer("Max. Wubook Avail",
                                default=_default_wmax_avail)
    wpushed = fields.Boolean("WuBook Pushed", readonly=True, default=False)

    @api.constrains('avail')
    def _check_avail(self):
        vroom_obj = self.env['hotel.virtual.room']
        cavail = len(vroom_obj.check_availability_virtual_room(
            self.date,
            self.date,
            virtual_room_id=self.virtual_room_id.id))
        max_avail = min(cavail,
                        self.virtual_room_id.total_rooms_count)
        if self.avail > max_avail:
            self.env['wubook.issue'].sudo().create({
                'section': 'avail',
                'message': _("The new availability can't be greater than \
                    the actual availability \
                    \n[%s]\nInput: %d\Limit: %d") % (self.virtual_room_id.name,
                                                    self.avail,
                                                    max_avail),
                'wid': self.virtual_room_id.wrid,
                'date_start': self.date,
                'date_end': self.date,
            })
            # Auto-Fix wubook availability
            date_dt = date_utils.get_datetime(self.date)
            self.env['wubook'].update_availability([{
                'id': self.virtual_room_id.wrid,
                'days': [{
                    'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    'avail': max_avail,
                }],
            }])
        return super(VirtualRoomAvailability, self)._check_avail()

    @api.constrains('wmax_avail')
    def _check_wmax_avail(self):
        if self.wmax_avail > self.virtual_room_id.total_rooms_count:
            raise ValidationError(_("max avail for wubook can't be high \
                than toal rooms \
                count: %d") % self.virtual_room_id.total_rooms_count)

    @api.onchange('virtual_room_id')
    def onchange_virtual_room_id(self):
        if self.virtual_room_id:
            self.wmax_avail = self.virtual_room_id.max_real_rooms

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            vals.update({'wpushed': False})
        return super(VirtualRoomAvailability, self).write(vals)

    @api.model
    def refresh_availability(self, checkin, checkout, product_id):
        date_start = date_utils.get_datetime(checkin)
        # Not count end day of the reservation
        date_diff = date_utils.date_diff(checkin, checkout, hours=False)

        vroom_obj = self.env['hotel.virtual.room']
        virtual_room_avail_obj = self.env['hotel.virtual.room.availability']

        vrooms = vroom_obj.search([
            ('room_ids.product_id', '=', product_id)
        ])
        for vroom in vrooms:
            if vroom.wrid and vroom.wrid != '':
                for i in range(0, date_diff):
                    ndate_dt = date_start + timedelta(days=i)
                    ndate_str = ndate_dt.strftime(
                                                DEFAULT_SERVER_DATE_FORMAT)
                    avail = len(vroom_obj.check_availability_virtual_room(
                        ndate_str,
                        ndate_str,
                        virtual_room_id=vroom.id))
                    max_avail = vroom.max_real_rooms
                    vroom_avail_id = virtual_room_avail_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', ndate_str)], limit=1)
                    if vroom_avail_id and vroom_avail_id.wmax_avail >= 0:
                        max_avail = vroom_avail_id.wmax_avail
                    avail = max(
                            min(avail, vroom.total_rooms_count, max_avail), 0)

                    if vroom_avail_id:
                        vroom_avail_id.write({'avail': avail})
                    else:
                        virtual_room_avail_obj.create({
                            'virtual_room_id': vroom.id,
                            'date': ndate_str,
                            'avail': avail,
                        })
