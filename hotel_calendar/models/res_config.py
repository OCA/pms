# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

class HotelConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

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

    color_letter_pre_reservation = fields.Char('Letter  Pre-reservation', default='#FFFFFF')
    color_letter_reservation = fields.Char('Letter  Confirmed Reservation ', default='#FFFFFF')
    color_letter_reservation_pay = fields.Char('Letter Paid Reservation', default='#FFFFFF')
    color_letter_stay = fields.Char('Letter Checkin', default='#FFFFFF')
    color_letter_stay_pay = fields.Char('Letter Stay Pay', default='#FFFFFF')
    color_letter_checkout = fields.Char('Letter Checkout', default='#FFFFFF')
    color_letter_dontsell = fields.Char('Letter Dont Sell', default='#FFFFFF')
    color_letter_staff = fields.Char('Letter Staff', default='#FFFFFF')
    color_letter_to_assign = fields.Char('Letter Ota to Assign', default='#FFFFFF')
    color_letter_payment_pending = fields.Char('Letter Payment Pending', default='#FFFFFF')

    @api.multi
    def set_values(self):
        super(HotelConfiguration, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("hotel_calendar.color_pre_reservation", self.color_pre_reservation)
        ICPSudo.set_param("hotel_calendar.color_reservation", self.color_reservation)
        ICPSudo.set_param("hotel_calendar.color_reservation_pay", self.color_reservation_pay)
        ICPSudo.set_param("hotel_calendar.color_stay", self.color_stay)
        ICPSudo.set_param("hotel_calendar.color_stay_pay", self.color_stay_pay)
        ICPSudo.set_param("hotel_calendar.color_checkout", self.color_checkout)
        ICPSudo.set_param("hotel_calendar.color_dontsell", self.color_dontsell)
        ICPSudo.set_param("hotel_calendar.color_staff", self.color_staff)
        ICPSudo.set_param("hotel_calendar.color_to_assign", self.color_to_assign)
        ICPSudo.set_param("hotel_calendar.color_payment_pending", self.color_payment_pending)

        ICPSudo.set_param("hotel_calendar.color_letter_pre_reservation", self.color_letter_pre_reservation)
        ICPSudo.set_param("hotel_calendar.color_letter_reservation", self.color_letter_reservation)
        ICPSudo.set_param("hotel_calendar.color_letter_reservation_pay", self.color_letter_reservation_pay)
        ICPSudo.set_param("hotel_calendar.color_letter_stay", self.color_letter_stay)
        ICPSudo.set_param("hotel_calendar.color_letter_stay_pay", self.color_letter_stay_pay)
        ICPSudo.set_param("hotel_calendar.color_letter_checkout", self.color_letter_checkout)
        ICPSudo.set_param("hotel_calendar.color_letter_dontsell", self.color_letter_dontsell)
        ICPSudo.set_param("hotel_calendar.color_letter_staff", self.color_letter_staff)
        ICPSudo.set_param("hotel_calendar.color_letter_to_assign", self.color_letter_to_assign)
        ICPSudo.set_param("hotel_calendar.color_letter_payment_pending", self.color_letter_payment_pending)

    @api.model
    def get_values(self):
        res = super(HotelConfiguration, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            color_pre_reservation=ICPSudo.get_param('hotel_calendar.color_pre_reservation', default='#A24680'),
            color_reservation=ICPSudo.get_param('hotel_calendar.color_reservation', default='#7C7BAD'),
            color_reservation_pay=ICPSudo.get_param('hotel_calendar.color_reservation_pay', default='#584D76'),
            color_stay=ICPSudo.get_param('hotel_calendar.color_stay', default='#FF4040'),
            color_stay_pay=ICPSudo.get_param('hotel_calendar.color_stay_pay', default='#82BF07'),
            color_checkout=ICPSudo.get_param('hotel_calendar.color_checkout', default='#7E7E7E'),
            color_dontsell=ICPSudo.get_param('hotel_calendar.color_dontsell', default='#000000'),
            color_staff=ICPSudo.get_param('hotel_calendar.color_staff', default='#C08686'),
            color_to_assign=ICPSudo.get_param('hotel_calendar.color_to_assign', default='#ED722E'),
            color_payment_pending=ICPSudo.get_param('hotel_calendar.color_payment_pending', default='#A24689'),
            color_letter_pre_reservation=ICPSudo.get_param('hotel_calendar.color_letter_pre_reservation', default='#FFFFFF'),
            color_letter_reservation=ICPSudo.get_param('hotel_calendar.color_letter_reservation', default='#FFFFFF'),
            color_letter_reservation_pay=ICPSudo.get_param('hotel.color_letter_reservation_pay', default='#FFFFFF'),
            color_letter_stay=ICPSudo.get_param('hotel_calendar.color_letter_stay', default='#FFFFFF'),
            color_letter_stay_pay=ICPSudo.get_param('hotel_calendar.color_letter_stay_pay', default='#FFFFFF'),
            color_letter_checkout=ICPSudo.get_param('hotel_calendar.color_letter_checkout', default='#FFFFFF'),
            color_letter_dontsell=ICPSudo.get_param('hotel_calendar.color_letter_dontsell', default='#FFFFFF'),
            color_letter_staff=ICPSudo.get_param('hotel_calendar.color_letter_staff', default='#FFFFFF'),
            color_letter_to_assign=ICPSudo.get_param('hotel_calendar.color_letter_to_assign', default='#FFFFFF'),
            color_letter_payment_pending=ICPSudo.get_param('hotel_calendar.color_letter_payment_pending', default='#FFFFFF'),
        )
        return res
