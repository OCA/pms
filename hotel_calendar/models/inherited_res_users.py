# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    pms_divide_rooms_by_capacity = fields.Boolean('Divide rooms by capacity',
                                                  default=True)
    pms_end_day_week = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday')
    ], string='End day of week', default='6')
    pms_end_day_week_offset = fields.Selection([
        ('0', '0 Days'),
        ('1', '1 Days'),
        ('2', '2 Days'),
        ('3', '3 Days'),
        ('4', '4 Days'),
        ('5', '5 Days'),
        ('6', '6 Days')
    ], string='Also illuminate the previous', default='0')
    pms_type_move = fields.Selection([
        ('normal', 'Normal'),
        ('assisted', 'Assisted'),
        ('allow_invalid', 'Allow Invalid')
    ], string='Reservation move mode', default='normal')
    pms_default_num_days = fields.Selection([
        ('month', '1 Month'),
        ('21', '3 Weeks'),
        ('14', '2 Weeks'),
        ('7', '1 Week')
    ], string='Default number of days', default='month')

    pms_show_notifications = fields.Boolean('Show Notifications', default=True)
    pms_show_pricelist = fields.Boolean('Show Pricelist', default=True)
    pms_show_availability = fields.Boolean('Show Availability', default=True)
    pms_show_num_rooms = fields.Integer('Show Num. Rooms', default=0)

    pms_allowed_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Allow Calander Event Tags")
    pms_denied_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Deny Calander Event Tags")

    npms_end_day_week = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday')
    ], string='End day of week', default='6')
    npms_end_day_week_offset = fields.Selection([
        ('0', '0 Days'),
        ('1', '1 Days'),
        ('2', '2 Days'),
        ('3', '3 Days'),
        ('4', '4 Days'),
        ('5', '5 Days'),
        ('6', '6 Days')
    ], string='Also illuminate the previous', default='0')
    npms_default_num_days = fields.Selection([
        ('month', '1 Month'),
        ('21', '3 Weeks'),
        ('14', '2 Weeks'),
        ('7', '1 Week')
    ], string='Default number of days', default='month')

    npms_allowed_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Allow Calander Event Tags")
    npms_denied_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Deny Calander Event Tags")

    color_pre_reservation = fields.Char('Pre-reservation', default='#A24680')
    color_reservation = fields.Char('Confirmed Reservation ', default='#7C7BAD')
    color_reservation_pay = fields.Char('Paid Reservation', default='#7C7BAD')
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

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights.
        Access rights are disabled by default, but allowed on some specific
        fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        super(ResUsers, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend([
            'pms_divide_rooms_by_capacity',
            'pms_end_day_week',
            'pms_end_day_week_offset',
            'pms_type_move',
            'pms_default_num_days',
            'pms_show_notifications',
            'pms_show_pricelist',
            'pms_show_availability',
            'pms_show_num_rooms',
            'pms_allowed_events_tags',
            'pms_denied_events_tags',
            'npms_end_day_week',
            'npms_end_day_week_offset',
            'npms_default_num_days',
            'npms_allowed_events_tags',
            'npms_denied_events_tags',
            'color_pre_reservation',
            'color_reservation',
            'color_reservation_pay',
            'color_stay',
            'color_stay_pay',
            'color_checkout',
            'color_dontsell',
            'color_staff',
            'color_to_assign',
            'color_payment_pending',
            'color_letter_pre_reservation',
            'color_letter_reservation',
            'color_letter_reservation_pay',
            'color_letter_stay',
            'color_letter_stay_pay',
            'color_letter_checkout',
            'color_letter_dontsell',
            'color_letter_staff',
            'color_letter_to_assign',
            'color_letter_payment_pending',
        ])
        # duplicate list to avoid modifying the original reference
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend([
            'pms_divide_rooms_by_capacity',
            'pms_end_day_week',
            'pms_end_day_week_offset',
            'pms_type_move',
            'pms_default_num_days',
            'pms_show_notifications',
            'pms_show_pricelist',
            'pms_show_availability',
            'pms_show_num_rooms',
            'pms_allowed_events_tags',
            'pms_denied_events_tags',
            'npms_end_day_week',
            'npms_end_day_week_offset',
            'npms_default_num_days',
            'npms_allowed_events_tags',
            'npms_denied_events_tags',
            'color_pre_reservation',
            'color_reservation',
            'color_reservation_pay',
            'color_stay',
            'color_stay_pay',
            'color_checkout',
            'color_dontsell',
            'color_staff',
            'color_to_assign',
            'color_payment_pending',
            'color_letter_pre_reservation',
            'color_letter_reservation',
            'color_letter_reservation_pay',
            'color_letter_stay',
            'color_letter_stay_pay',
            'color_letter_checkout',
            'color_letter_dontsell',
            'color_letter_staff',
            'color_letter_to_assign',
            'color_letter_payment_pending',
        ])
