# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api

class HotelRoomTypeClass(models.Model):
    """ Before creating a 'room type_class', you need to consider the following:
    With the term 'room type class' is meant a physicial class of
    residential accommodation: for example, a Room, a Bed, an Apartment,
    a Tent, a Caravan...
    """
    _name = "hotel.room.type.class"
    _description = "Room Type Class"
    _order = "sequence, code_class, name"
    _sql_constraints = [('code_type_unique', 'unique(code_type)',
                         'code must be unique!')]

    name = fields.Char('Class Name', required=True, translate=True)
    room_type_ids = fields.One2many('hotel.room.type', 'class_id', 'Types')
    active = fields.Boolean('Active', default=True,
                            help="The active field allows you to hide the \
                            category without removing it.")
    sequence = fields.Integer('Sequence', default=0)
    code_class = fields.Char('Code')
