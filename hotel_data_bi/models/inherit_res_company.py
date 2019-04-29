# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Inherit_res_company(models.Model):
    _inherit = 'res.company'

    id_hotel = fields.Integer(
        'Unique ID for DataBI', default=0,
        help='It must be unique to be able to identify the hotel, \
        within a hotel group.')
