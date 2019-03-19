# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.exceptions import ValidationError
from datetime import timedelta
from openerp import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


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

        hotel_room_type_obj = self.env['hotel.room.type']

        cmds_reservation_lines = []
        for rline in reservation_id.reservation_lines:
            cmds_reservation_lines.append((0, False, {
                'date': rline.date,
                'price': rline.price,
            }))

        # Check Input
        avails = hotel_room_type_obj.check_availability_room_type(
            reservation_id.checkin,
            (fields.Date.from_string(reservation_id.checkout) -
                timedelta(days=1)).strftime(
                    DEFAULT_SERVER_DATE_FORMAT
                    ),
            room_type_id=reservation_id.room_type_id.id)
        total_free_rooms = len(avails)

        if total_free_rooms < self.num:
            raise ValidationError(_("Too much duplicated reservations! \
                                    There are no '%d' free rooms") % self.num)

        for i in range(0, self.num):
            free_rooms = hotel_room_type_obj.check_availability_room_type(
                reservation_id.checkin,
                (fields.Date.from_string(reservation_id.checkout) -
                    timedelta(days=1)).strftime(
                        DEFAULT_SERVER_DATE_FORMAT
                        ),
                room_type_id=reservation_id.room_type_id.id)
            if any(free_rooms):
                new_reservation_id = hotel_reservation_obj.create({
                    'room_id': free_rooms[0].id,
                    'room_type_id': free_rooms[0].room_type_id.id,
                    'folio_id': reservation_id.folio_id.id,
                    'checkin': reservation_id.checkin,
                    'checkout': reservation_id.checkout,
                    'adults': reservation_id.adults,
                    'children': reservation_id.children,
                    'name': reservation_id.name,
                    'reservation_lines': cmds_reservation_lines,
                })
                if new_reservation_id:
                    rpartner_id = reservation_id.order_id.partner_id
                    new_reservation_id.order_id.partner_id = rpartner_id
                break
            else:
                raise ValidationError(_("Unexpected Error: Can't found a \
                                        free room"))
        return True
