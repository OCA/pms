# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class MassivePriceChangeWizard(models.TransientModel):
    _name = 'hotel.wizard.massive.price.reservation.days'

    new_price = fields.Float('New Price', default=1, min=1)

    @api.multi
    def massive_price_change_days(self):
        self.ensure_one()
        hotel_reservation_obj = self.env['hotel.reservation']
        reservation_id = hotel_reservation_obj.browse(
            self.env.context.get('active_id'))
        if not reservation_id:
            return False

        cmds = []
        for rline in reservation_id.reservation_lines:
            cmds.append((
                1,
                rline.id,
                {
                    'price': self.new_price
                }
            ))
        reservation_id.write({
            'reservation_lines': cmds
        })
        # FIXME: For some reason need force reservation price calcs
        reservation_id._computed_amount_reservation()
        # FIXME: Workaround for dispatch updated price
        reservation_id.folio_id.write({
            'room_lines': [
                (
                    1,
                    reservation_id.id, {
                        'reservation_lines': cmds
                    }
                )
            ]
        })

        return True
