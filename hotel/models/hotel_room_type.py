# -*- coding: utf-8 -*-
# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from decimal import Decimal
from datetime import datetime, timedelta
import dateutil.parser
# For Python 3.0 and later
from urllib.request import urlopen
import time
from odoo.exceptions import except_orm, UserError, ValidationError
from odoo.tools import (
    misc,
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo import models, fields, api, _
from odoo.addons.hotel import date_utils

class HotelRoomType(models.Model):
    """ Before creating a 'room type', you need to consider the following:
    With the term 'room type' is meant a type of residential accommodation: for
    example, a Double Room, a Economic Room, an Apartment, a Tent, a Caravan...
    """
    _name = "hotel.room.type"
    _description = "Room Type"

    _inherits = {'product.product': 'product_id'}
    # Relationship between models
    product_id = fields.Many2one('product.product', 'Product Room Type',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    room_ids = fields.One2many('hotel.room', 'room_type_id', 'Rooms')

    # TODO Hierarchical relationship for parent-child tree ?
    # parent_id = fields.Many2one ...

    # Used for activate records
    active = fields.Boolean('Active', default=True,
                            help="The active field allows you to hide the \
                            category without removing it.")
    # Used for ordering
    sequence = fields.Integer('Sequence', default=0)

    code_type = fields.Char('Code')

    _order = "sequence, code_type, name"

    _sql_constraints = [('code_type_unique', 'unique(code_type)',
                         'code must be unique!')]
    # total number of rooms in this type
    total_rooms_count = fields.Integer(compute='_compute_total_rooms')

    @api.depends('room_ids')
    def _compute_total_rooms(self):
        for record in self:
            record.total_rooms_count = len(record.room_ids)

    def _check_duplicated_rooms(self):
        # FIXME Using a Many2one relationship duplicated should not been possible
        pass

    @api.multi
    def get_capacity(self):
        # WARNING use selg.capacity directly ?
        pass
        # self.ensure_one()
        # hotel_room_obj = self.env['hotel.room']
        # room_categories = self.room_type_ids.mapped('room_ids.id')
        # room_ids = self.room_ids + hotel_room_obj.search([
        #     ('categ_id.id', 'in', room_categories)
        # ])
        # capacities = room_ids.mapped('capacity')
        # return any(capacities) and min(capacities) or 0

    @api.model
    # TODO Rename to check_availability_room_type
    def check_availability_virtual_room(self, dfrom, dto,
                                        room_type_id=False, notthis=[]):
        """
        Check the avalability for an specific type of room
        @param self: The object pointer
        @param dfrom: Range date from
        @param dto: Range date to
        @param room_type_id: Room Type
        @param notthis: Array excluding Room Types
        @return: A recordset of free rooms ?
        """
        reservations = self.env['hotel.reservation'].get_reservations(dfrom, dto)
        reservations_rooms = reservations.mapped('room_id.id')
        free_rooms = self.env['hotel.room'].search([
            ('id', 'not in', reservations_rooms),
            ('id', 'not in', notthis)
        ])
        if room_type_id:
            room_type_id = self.env['hotel.room.type'].search([
                ('id', '=', room_type_id)
            ])
            # QUESTION What linked represent? Rooms in this type ? 
            rooms_linked = self.room_ids
            free_rooms = free_rooms & rooms_linked
        return free_rooms.sorted(key=lambda r: r.sequence)

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel room type.
        """
        vals.update({'is_room_type': True})
        vals.update({'purchase_ok': False})
        vals.update({'type': 'service'})
        return super().create(vals)

    @api.multi
    def unlink(self):
        for record in self:
            record.product_id.unlink()
        return super().unlink()
