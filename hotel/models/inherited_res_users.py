# Copyright 2019 Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _get_default_hotel(self):
        return self.env.user.hotel_id

    hotel_id = fields.Many2one('hotel.property', string='Hotel', default=_get_default_hotel,
                               help='The hotel this user is currently working for.',
                               context={'user_preference': True})
    hotel_ids = fields.Many2many('hotel.property', 'hotel_property_users_rel', 'user_id', 'hotel_id',
                                 string='Hotels', default=_get_default_hotel)
