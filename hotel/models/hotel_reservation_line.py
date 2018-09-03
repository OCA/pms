# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields
from odoo.addons import decimal_precision as dp

class HotelReservationLine(models.Model):
    _name = "hotel.reservation.line"
    _order = "date"

    reservation_id = fields.Many2one('hotel.reservation', string='Reservation',
                                     ondelete='cascade', required=True,
                                     copy=False)
    date = fields.Date('Date')
    price = fields.Float('Price')
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)
