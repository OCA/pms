# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
import pytz
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


@api.model
def _tz_get(self):
    # put POSIX 'Etc/*' entries at the end to avoid confusing users
    # see bug 1086728
    return [(tz, tz) for tz in sorted(pytz.all_timezones,
                                      key=lambda tz: tz
                                      if not tz.startswith('Etc/') else '_')]


class HotelConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    default_pricelist_id = fields.Many2one('product.pricelist',
                                          'Product Pricelist')
    default_restriction_id = fields.Many2one('hotel.room.type.restriction',
                                             'Restrictions')
    default_arrival_hour = fields.Char('Default Arrival Hour (GMT)',
                                       help="HH:mm Format", default="14:00")
    default_departure_hour = fields.Char('Default Departure Hour (GMT)',
                                         help="HH:mm Format", default="12:00")
    tz_hotel = fields.Selection(_tz_get, string='Timezone',
                                default=lambda self: self._context.get('tz'),
                                help="The hotel's timezone, used to manage \
                                    date and time values in reservations \
                                    It is important to set a value for this \
                                    field.")

    @api.multi
    def set_values(self):
        super(HotelConfiguration, self).set_values()

        self.env['ir.default'].sudo().set(
            'res.config.settings', 'default_pricelist_id',
            self.default_pricelist_id.id)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'default_restriction_id',
            self.default_restriction_id.id)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'tz_hotel', self.tz_hotel)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'default_arrival_hour',
            self.default_arrival_hour)
        self.env['ir.default'].sudo().set(
            'res.config.settings', 'default_departure_hour',
            self.default_departure_hour)

    @api.model
    def get_values(self):
        res = super(HotelConfiguration, self).get_values()

        # ONLY FOR v11. DO NOT FORWARD-PORT
        default_pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id')
        default_restriction_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_restriction_id')
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')
        res.update(
            default_pricelist_id=default_pricelist_id,
            default_restriction_id=default_restriction_id,
            tz_hotel=tz_hotel,
            default_arrival_hour=default_arrival_hour,
            default_departure_hour=default_departure_hour,
        )
        return res

    @api.constrains('default_arrival_hour', 'default_departure_hour')
    def _check_hours(self):
        r = re.compile('[0-2][0-9]:[0-5][0-9]')
        if not r.match(self.default_arrival_hour):
            raise ValidationError(_("Invalid arrival hour (Format: HH:mm)"))
        if not r.match(self.default_departure_hour):
            raise ValidationError(_("Invalid departure hour (Format: HH:mm)"))
