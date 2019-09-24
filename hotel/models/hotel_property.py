# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelProperty(models.Model):
    _name = 'hotel.property'
    _description = 'Hotel'
    _inherits = {'res.partner': 'partner_id'}

    # Fields declaration
    partner_id = fields.Many2one(
        'res.partner',
        'Hotel Property',
        required=True,
        delegate=True,
        ondelete='cascade')
    company_id = fields.Many2one(
        'res.company',
        required=True,
        help='The company that owns or operates this hotel.')
    user_ids = fields.Many2many(
        'res.users',
        'hotel_property_users_rel',
        'hotel_id',
        'user_id',
        string='Accepted Users')
    room_type_ids = fields.One2many(
        'hotel.room.type',
        'hotel_id',
        'Room Types')
    room_ids = fields.One2many(
        'hotel.room',
        'hotel_id',
        'Rooms')
    default_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Product Pricelist',
        required=True,
        help='The default pricelist used in this hotel.')
    default_restriction_id = fields.Many2one(
        'hotel.room.type.restriction',
        'Restriction Plan',
        required=True,
        help='The default restriction plan used in this hotel.')
    default_arrival_hour = fields.Char('Arrival Hour (GMT)',
                                       help="HH:mm Format", default="14:00")
    default_departure_hour = fields.Char('Departure Hour (GMT)',
                                         help="HH:mm Format", default="12:00")
    default_cancel_policy_days = fields.Integer('Cancellation Days')
    default_cancel_policy_percent = fields.Float('Percent to pay')

    # Constraints and onchanges
    @api.constrains('default_arrival_hour', 'default_departure_hour')
    def _check_hours(self):
        r = re.compile('[0-2][0-9]:[0-5][0-9]')
        if not r.match(self.default_arrival_hour):
            raise ValidationError(_("Invalid arrival hour (Format: HH:mm)"))
        if not r.match(self.default_departure_hour):
            raise ValidationError(_("Invalid departure hour (Format: HH:mm)"))
