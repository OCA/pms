# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api


class HotelCalendarManagement(models.TransientModel):
    _inherit = 'hotel.calendar.management'

    @api.model
    def _get_availability_values(self, avail, vroom):
        vals = super(HotelCalendarManagement, self)._get_availability_values(
                                                                avail, vroom)
        vals.update({'wmax_avail': vals['avail']})
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
