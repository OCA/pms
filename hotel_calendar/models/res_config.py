# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HotelConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    color_pre_reservation = fields.Char('Pre-reservation')
    color_reservation = fields.Char('Confirmed Reservation')
    color_reservation_pay = fields.Char('Paid Reservation')
    color_stay = fields.Char('Checkin')
    color_stay_pay = fields.Char('Paid Checkin')
    color_checkout = fields.Char('Checkout')
    color_dontsell = fields.Char('Dont Sell')
    color_staff = fields.Char('Staff')
    color_to_assign = fields.Char('Ota Reservation to Assign')
    color_payment_pending = fields.Char('Letter Payment Pending')
    color_letter_pre_reservation = fields.Char('Letter  Pre-reservation')
    color_letter_reservation = fields.Char('Letter  Confirmed Reservation')
    color_letter_reservation_pay = fields.Char('Letter Paid Reservation')
    color_letter_stay = fields.Char('Letter Checkin')
    color_letter_stay_pay = fields.Char('Letter Stay Pay')
    color_letter_checkout = fields.Char('Letter Checkout')
    color_letter_dontsell = fields.Char('Letter Dont Sell')
    color_letter_staff = fields.Char('Letter Staff')
    color_letter_to_assign = fields.Char('Letter Ota to Assign')
    color_letter_payment_pending = fields.Char('Letter Payment Pending')

    @api.multi
    def set_values(self):
        super(HotelConfiguration, self).set_values()
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_pre_reservation', self.color_pre_reservation)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_reservation', self.color_reservation)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_reservation_pay', self.color_reservation_pay)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_stay', self.color_stay)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_stay_pay', self.color_stay_pay)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_checkout', self.color_checkout)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_dontsell', self.color_dontsell)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_staff', self.color_staff)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_to_assign', self.color_to_assign)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_payment_pending', self.color_payment_pending)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_letter_pre_reservation', self.color_letter_pre_reservation)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_letter_reservation', self.color_letter_reservation)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_letter_reservation_pay', self.color_letter_reservation_pay)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_letter_stay', self.color_letter_stay)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_letter_stay_pay', self.color_letter_stay_pay)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_letter_checkout', self.color_letter_checkout)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_letter_dontsell', self.color_letter_dontsell)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_letter_staff', self.color_letter_staff)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'color_letter_to_assign', self.color_letter_to_assign)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'color_letter_payment_pending', self.color_letter_payment_pending)
        self.env['ir.default'].sudo().set(
            'res.config.settings',
            'default_arrival_hour', self.default_arrival_hour)

    @api.model
    def get_values(self):
        res = super(HotelConfiguration, self).get_values()

        # ONLY FOR v11. DO NOT FORWARD-PORT
        color_pre_reservation = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_pre_reservation', self.color_pre_reservation)
        color_reservation = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_reservation', self.color_reservation)
        color_reservation_pay = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_reservation_pay', self.color_reservation_pay)
        color_stay = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_stay', self.color_stay)
        color_stay_pay = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_stay_pay', self.color_stay_pay)
        color_checkout = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_checkout', self.color_checkout)
        color_dontsell = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_dontsell', self.color_dontsell)
        color_staff = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_staff', self.color_staff)
        color_to_assign = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_to_assign', self.color_to_assign)
        color_payment_pending = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_payment_pending', self.color_payment_pending)
        color_letter_pre_reservation = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_letter_pre_reservation', self.color_letter_pre_reservation)
        color_letter_reservation = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_letter_reservation', self.color_letter_reservation)
        color_letter_reservation_pay = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_letter_reservation_pay', self.color_letter_reservation_pay)
        color_letter_stay = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_letter_stay', self.color_letter_stay)
        color_letter_stay_pay = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_letter_stay_pay',
            self.color_letter_stay_pay)
        color_letter_checkout = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_letter_checkout',
            self.color_letter_checkout)
        color_letter_dontsell = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_letter_dontsell',
            self.color_letter_dontsell)
        color_letter_staff = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_letter_staff',
            self.color_letter_staff)
        color_letter_to_assign = self.env['ir.default'].sudo().get(
            'res.config.settings', 'color_letter_to_assign',
            self.color_letter_to_assign)
        color_letter_payment_pending = self.env['ir.default'].sudo().get(
            'res.config.settings',
            'color_letter_payment_pending', self.color_letter_payment_pending)
        res.update(
            color_pre_reservation=color_pre_reservation,
            color_reservation=color_reservation,
            color_reservation_pay=color_reservation_pay,
            color_stay=color_stay,
            color_stay_pay=color_stay_pay,
            color_checkout=color_checkout,
            color_dontsell=color_dontsell,
            color_staff=color_staff,
            color_to_assign=color_to_assign,
            color_payment_pending=color_payment_pending,
            color_letter_pre_reservation=color_letter_pre_reservation,
            color_letter_reservation=color_letter_reservation,
            color_letter_reservation_pay=color_letter_reservation_pay,
            color_letter_stay=color_letter_stay,
            color_letter_stay_pay=color_letter_stay_pay,
            color_letter_checkout=color_letter_checkout,
            color_letter_dontsell=color_letter_dontsell,
            color_letter_staff=color_letter_staff,
            color_letter_to_assign=color_letter_to_assign,
            color_letter_payment_pending=color_letter_payment_pending,
        )
        return res
