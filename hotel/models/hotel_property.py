# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields


class HotelProperty(models.Model):
    _name = 'hotel.property'
    _description = 'Hotel'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', 'Hotel Property',
                                 required=True, delegate=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', help='The company that owns or operates this hotel.')
    user_ids = fields.Many2many('res.users', 'hotel_property_users_rel', 'hotel_id', 'user_id',
                                string='Accepted Users')
