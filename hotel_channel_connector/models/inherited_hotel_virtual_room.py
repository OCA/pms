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
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class HotelVirtualRoom(models.Model):
    _inherit = 'hotel.virtual.room'

    @api.depends('wcapacity')
    @api.onchange('room_ids', 'room_type_ids')
    def _get_capacity(self):
        hotel_room_obj = self.env['hotel.room']
        for rec in self:
            rec.wcapacity = rec.get_capacity()

    wscode = fields.Char("WuBook Short Code", readonly=True)
    wrid = fields.Char("WuBook Room ID", readonly=True)
    wcapacity = fields.Integer("WuBook Capacity", default=1)

    @api.constrains('wcapacity')
    def _check_wcapacity(self):
        if self.wcapacity < 1:
            raise ValidationError(_("wcapacity can't be less than one"))

    @api.multi
    @api.constrains('wscode')
    def _check_wscode(self):
        if len(self.wscode) > 4:  # Wubook scode max. length
            raise ValidationError(_("SCODE Can't be longer than 4 characters"))

    @api.multi
    def get_restrictions(self, date):
        restriction_plan_id = int(self.env['ir.default'].sudo().get(
                            'hotel.config.settings', 'parity_restrictions_id'))
        self.ensure_one()
        restriction = self.env['hotel.virtual.room.restriction.item'].search([
            ('date_start', '=', date),
            ('date_end', '=', date),
            ('virtual_room_id', '=', self.id),
            ('restriction_id', '=', restriction_plan_id)
        ], limit=1)
        return restriction
        # if restriction:
        #     return restriction
        # else:
        #     vroom_rest_it_obj = self.env['hotel.virtual.room.restriction.item']
        #     global_restr = vroom_rest_it_obj.search([
        #         ('applied_on', '=', '1_global'),
        #         ('restriction_id', '=', restriction_plan_id)
        #     ], limit=1)
        #     if global_restr:
        #         return global_restr
        # return False

    @api.model
    def create(self, vals):
        vroom = super(HotelVirtualRoom, self).create(vals)
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            seq_obj = self.env['ir.sequence']
            shortcode = seq_obj.next_by_code('hotel.virtual.room')[:4]
            wrid = self.env['wubook'].create_room(
                shortcode,
                vroom.name,
                vroom.wcapacity,
                vroom.list_price,
                vroom.max_real_rooms
            )
            if not wrid:
                raise ValidationError(_("Can't create room on WuBook"))
            vroom.with_context(wubook_action=False).write({
                'wrid': wrid,
                'wscode': shortcode,
            })
        return vroom

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            wubook_obj = self.env['wubook']
            for record in self:
                if record.wrid and record.wrid != '':
                    wres = wubook_obj.modify_room(
                        vals.get('wrid', record.wrid),
                        vals.get('name', record.name),
                        vals.get('wcapacity', record.wcapacity),
                        vals.get('list_price', record.list_price),
                        vals.get('max_real_rooms', record.max_real_rooms),
                        vals.get('wscode', record.wscode))
                    if not wres:
                        raise ValidationError(_("Can't modify room on WuBook"))
        return super(HotelVirtualRoom, self).write(vals)

    @api.multi
    def unlink(self):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            for record in self:
                if record.wrid and record.wrid != '':
                    wres = self.env['wubook'].delete_room(record.wrid)
                    if not wres:
                        raise ValidationError(_("Can't delete room on WuBook"))
        return super(HotelVirtualRoom, self).unlink()

    @api.multi
    def import_rooms(self):
        return self.env['wubook'].import_rooms()
