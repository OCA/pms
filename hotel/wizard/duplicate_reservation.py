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
from datetime import datetime, timedelta
from openerp.exceptions import ValidationError
from openerp import models, fields, api, _
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)


class DuplicateReservationWizard(models.TransientModel):
    _name = 'hotel.wizard.duplicate.reservation'

    num = fields.Integer('Num. New Reservations', default=1, min=1)

    @api.multi
    def duplicate_reservation(self):
        self.ensure_one()
        hotel_reservation_obj = self.env['hotel.reservation']
        reservation_id = hotel_reservation_obj.browse(
            self.env.context.get('active_id'))
        if not reservation_id:
            return False

        if reservation_id.splitted:
            raise ValidationError(_("Can't duplicate splitted reservations"))

        hotel_room_obj = self.env['hotel.room']
        hotel_vroom_obj = self.env['hotel.virtual.room']

        room_id = hotel_room_obj.search([
            ('product_id', '=', reservation_id.product_id.id)
        ], limit=1)
        vroom_ids = hotel_vroom_obj.search([
            '|', ('room_ids', 'in', [room_id.id]),
                 ('room_type_ids', 'in', [room_id.categ_id.id])
        ])

        cmds_reservation_lines = []
        for rline in reservation_id.reservation_lines:
            cmds_reservation_lines.append((0, False, {
                'date': rline.date,
                'price': rline.price,
            }))

        # Check Input
        total_free_rooms = 0
        for vroom in vroom_ids:
            avails = otel_vroom_obj.check_availability_virtual_room(
                reservation_id.checkin,
                reservation_id.checkout,
                virtual_room_id=vroom.id)
            total_free_rooms += len(avails)

        if total_free_rooms < self.num:
            raise ValidationError(_("Too much duplicated reservations! \
                                    There are no '%d' free rooms") % self.num)

        for i in range(0, self.num):
            for vroom in vroom_ids:
                free_rooms = hotel_vroom_obj.check_availability_virtual_room(
                    reservation_id.checkin,
                    reservation_id.checkout,
                    virtual_room_id=vroom.id)
                if any(free_rooms):
                    new_reservation_id = hotel_reservation_obj.create({
                        'product_id': free_rooms[0].product_id.id,
                        'folio_id': reservation_id.folio_id.id,
                        'checkin': reservation_id.checkin,
                        'checkout': reservation_id.checkout,
                        'adults': reservation_id.adults,
                        'children': reservation_id.children,
                        'name': reservation_id.name,
                        'reservation_lines': cmds_reservation_lines,
                        'price_unit': reservation_id.price_unit,
                    })
                    if new_reservation_id:
                        rpartner_id = reservation_id.order_id.partner_id
                        new_reservation_id.order_id.partner_id = rpartner_id
                    break
                else:
                    raise ValidationError(_("Unexpected Error: Can't found a \
                                            free room"))
        return True
