# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Dario Lodeiros <>
#                       Alexandre Díaz <dev@redneboa.es>
#
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
from decimal import Decimal
from datetime import datetime, timedelta
import dateutil.parser
# For Python 3.0 and later
from urllib.request import urlopen
import time
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp.tools import (
    misc,
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from openerp import models, fields, api, _
from odoo.addons.hotel import date_utils


class VirtualRoom(models.Model):
    _name = 'hotel.virtual.room'
    _inherits = {'product.product': 'product_id'}

    @api.depends('room_ids', 'room_type_ids')
    def _compute_total_rooms(self):
        for r in self:
            count = 0
            count += len(r.room_ids)    # Rooms linked directly
            room_categories = r.room_type_ids.mapped('room_ids.id')
            count += self.env['hotel.room'].search_count([
                ('categ_id.id', 'in', room_categories)
            ])  # Rooms linked through room type
            r.total_rooms_count = count

    @api.constrains('room_ids', 'room_type_ids')
    def _check_duplicated_rooms(self):
        warning_msg = ""
        for r in self:
            room_categories = self.room_type_ids.mapped('room_ids.id')
            if self.room_ids & self.env['hotel.room'].search([
                    ('categ_id.id', 'in', room_categories)]):
                room_ids = self.room_ids & self.env['hotel.room'].search([
                    ('categ_id.id', 'in', room_categories)
                ])
                rooms_name = ','.join(str(x.name) for x in room_ids)
                warning_msg += _('You can not enter the same room in duplicate \
                                    (check the room types) %s') % rooms_name
                raise models.ValidationError(warning_msg)

    @api.constrains('max_real_rooms', 'room_ids', 'room_type_ids')
    def _check_max_rooms(self):
        warning_msg = ""
        for r in self:
            if self.max_real_rooms > self.total_rooms_count:
                warning_msg += _('The Maxime rooms allowed can not be greate \
                                    than total rooms count')
                raise models.ValidationError(warning_msg)

    virtual_code = fields.Char('Code') # not used
    room_ids = fields.Many2many('hotel.room', string='Rooms')
    room_type_ids = fields.Many2many('hotel.room.type', string='Room Types')
    total_rooms_count = fields.Integer(compute='_compute_total_rooms')
    product_id = fields.Many2one('product.product', 'Product_id',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    # FIXME services are related to real rooms
    service_ids = fields.Many2many('hotel.services',
                                   string='Included Services')
    max_real_rooms = fields.Integer('Default Max Room Allowed')
    product_id = fields.Many2one(
        'product.product', required=True,
        ondelete='cascade')
    active = fields.Boolean(default=True, help="The active field allows you to hide the category without removing it.")

    @api.multi
    def get_capacity(self):
        self.ensure_one()
        hotel_room_obj = self.env['hotel.room']
        room_categories = self.room_type_ids.mapped('room_ids.id')
        room_ids = self.room_ids + hotel_room_obj.search([
            ('categ_id.id', 'in', room_categories)
        ])
        capacities = room_ids.mapped('capacity')
        return any(capacities) and min(capacities) or 0

    @api.model
    def check_availability_virtual_room(self, checkin, checkout,
                                        virtual_room_id=False, notthis=[]):
        occupied = self.env['hotel.reservation'].occupied(checkin, checkout)
        rooms_occupied = occupied.mapped('product_id.id')
        free_rooms = self.env['hotel.room'].search([
            ('product_id.id', 'not in', rooms_occupied),
            ('id', 'not in', notthis)
        ])
        if virtual_room_id:
            hotel_room_obj = self.env['hotel.room']
            virtual_room = self.env['hotel.virtual.room'].search([
                ('id', '=', virtual_room_id)
            ])
            room_categories = virtual_room.room_type_ids.mapped('room_ids.id')
            rooms_linked = virtual_room.room_ids | hotel_room_obj.search([
                ('categ_id.id', 'in', room_categories)])
            free_rooms = free_rooms & rooms_linked
        return free_rooms.sorted(key=lambda r: r.sequence)

    @api.multi
    def unlink(self):
        for record in self:
            # Set fixed price to rooms with price from this virtual rooms
            rooms = self.env['hotel.room'].search([
                ('sale_price_type', '=', 'vroom'),
                ('price_virtual_room', '=', record.id)
            ])
            for room in rooms:
                room.sale_price_type = 'fixed'
            # Remove product.product
            record.product_id.unlink()
        return super(VirtualRoom, self).unlink()
