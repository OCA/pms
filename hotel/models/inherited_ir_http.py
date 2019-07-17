# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super().session_info()
        user = request.env.user
        display_switch_hotel_menu = len(user.hotel_ids) > 1
        res['hotel_id'] = request.env.user.hotel_id.id if request.session.uid else None
        res['user_hotels'] = {'current_hotel': (user.hotel_id.id, user.hotel_id.name),
                              'allowed_hotels': [(hotel.id, hotel.name) for hotel in
                                                 user.hotel_ids]} if display_switch_hotel_menu else False
        return res
