# Copyright 2019  Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Fields declaration
    color_pre_reservation = fields.Char('Pre-reservation', default='#A24680')
    color_reservation = fields.Char('Confirmed Reservation ', default='#7C7BAD')
    color_reservation_pay = fields.Char('Paid Reservation', default='#584D76')
    color_stay = fields.Char('Checkin', default='#FF4040')
    color_stay_pay = fields.Char('Paid Checkin', default='#82BF07')
    color_checkout = fields.Char('Checkout', default='#7E7E7E')
    color_dontsell = fields.Char('Dont Sell', default='#000000')
    color_staff = fields.Char('Staff', default='#C08686')
    color_to_assign = fields.Char('Ota Reservation to Assign', default='#ED722E')
    color_payment_pending = fields.Char('Payment Pending', default='#A24689')
    color_letter_pre_reservation = fields.Char('Letter Pre-reservation', default='#FFFFFF')
    color_letter_reservation = fields.Char('Letter Confirmed Reservation ', default='#FFFFFF')
    color_letter_reservation_pay = fields.Char('Letter Paid Reservation', default='#FFFFFF')
    color_letter_stay = fields.Char('Letter Checkin', default='#FFFFFF')
    color_letter_stay_pay = fields.Char('Letter Stay Pay', default='#FFFFFF')
    color_letter_checkout = fields.Char('Letter Checkout', default='#FFFFFF')
    color_letter_dontsell = fields.Char('Letter Dont Sell', default='#FFFFFF')
    color_letter_staff = fields.Char('Letter Staff', default='#FFFFFF')
    color_letter_to_assign = fields.Char('Letter Ota to Assign', default='#FFFFFF')
    color_letter_payment_pending = fields.Char('Letter Payment Pending', default='#FFFFFF')
