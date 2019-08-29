# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    pms_show_notifications = fields.Boolean('Show Notifications', default=True)
    pms_show_pricelist = fields.Boolean('Show Pricelist', default=True)
    pms_show_availability = fields.Boolean('Show Availability', default=True)
    # TODO Allow calendar events? by user / by hotel / by company ?
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
        string="Allow Calandar Event Tags")
    npms_denied_events_tags = fields.Many2many(
        'calendar.event.type',
        string="Deny Calandar Event Tags")

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights.
        Access rights are disabled by default, but allowed on some specific
        fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        super(ResUsers, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend([
            'pms_show_notifications',
            'pms_show_pricelist',
            'pms_show_availability',
        ])
        # duplicate list to avoid modifying the original reference
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend([
            'pms_show_notifications',
            'pms_show_pricelist',
            'pms_show_availability',
        ])
