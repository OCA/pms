# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class HotelCalendarManagement(models.TransientModel):
    _inherit = 'hotel.calendar.management'

    @api.model
    def _get_availability_values(self, avail, room_type):
        vals = super(HotelCalendarManagement, self)._get_availability_values(
            avail, room_type)
        vals.update({
            'wmax_avail': vals['avail'],
            'no_ota': vals['no_ota'],
            'booked': vals['booked'],
        })
        return vals

    @api.model
    def _generate_avalaibility_data(self, room_type, date, avail):
        vals = super(HotelCalendarManagement, self)._generate_avalaibility_data(
            room_type, date, avail)
        vals.update({
            'no_ota': avail and avail.no_ota or False,
        })
        return vals

    @api.multi
    def save_changes(self, pricelist_id, restriction_id, pricelist,
                     restrictions, availability):
        res = super(HotelCalendarManagement, self).save_changes(
            pricelist_id,
            restriction_id,
            pricelist,
            restrictions,
            availability)
        self.env['wubook'].push_changes()
        return res
