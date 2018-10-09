# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, api
from odoo.addons.hotel_calendar.controllers.bus import HOTEL_BUS_CHANNEL_ID


class BusHotelCalendar(models.TransientModel):
    _name = 'bus.hotel.calendar'

    '''
    action:
        - create
        - write
        - unlink
        - cancelled
    ntype:
        - notif : Show a normal notification
        - warn : Show a warning notification
        - noshow : Don't show any notification
    '''
    @api.model
    def _generate_reservation_notif(self, vals):
        user_id = self.env['res.users'].browse(self.env.uid)
        master_reserv = vals['parent_reservation'] or vals['reserv_id']
        num_split = self.env['hotel.reservation'].search_count([
            ('folio_id', '=', vals['folio_id']),
            '|', ('parent_reservation', '=', master_reserv),
            ('id', '=', master_reserv),
            ('splitted', '=', True),
        ])

        return {
            'type': 'reservation',
            'action': vals['action'],
            'subtype': vals['type'],
            'title': vals['title'],
            'username': user_id.partner_id.name,
            'userid': user_id.id,
            'reservation': {
                'id': vals['id'],
                'reserv_id': vals['reserv_id'],
                'partner_name': vals['partner_name'],
                'adults': vals['adults'],
                'childer': vals['children'],
                'checkin': vals['checkin'],
                'checkout': vals['checkout'],
                'folio_id': vals['folio_id'],
                'reserve_color': vals['reserve_color'],
                'reserve_color_text': vals['reserve_color_text'],
                'splitted': vals['splitted'],
                'parent_reservation': vals['parent_reservation'],
                'room_name': vals['room_name'],
                'state': vals['state'],
                'only_read': False,
                'fix_days': vals['fix_days'],
                'fix_rooms': False,
                'overbooking': vals['overbooking'],
            },
            'tooltip': [
                vals['partner_name'],
                vals['partner_phone'],
                vals['checkin'],
                num_split,
                vals['price'],
            ]
        }

    @api.model
    def _generate_pricelist_notification(self, vals):
        date_dt = datetime.strptime(vals['date'], DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'pricelist',
            'price': {
                vals['pricelist_id']: [{
                    'days': {
                        date_dt.strftime("%d/%m/%Y"): vals['price'],
                    },
                    'room': vals['room_id'],
                    'id': vals['id'],
                }],
            },
        }

    @api.model
    def _generate_restriction_notification(self, vals):
        date_dt = datetime.strptime(vals['date'], DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'restriction',
            'restriction': {
                vals['room_id']: {
                    date_dt.strftime("%d/%m/%Y"): [
                        vals['min_stay'],
                        vals['min_stay_arrival'],
                        vals['max_stay'],
                        vals['max_stay_arrival'],
                        vals['closed'],
                        vals['closed_arrival'],
                        vals['closed_departure'],
                        vals['id'],
                    ],
                },
            },
        }

    @api.model
    def _generate_availability_notification(self, vals):
        date_dt = datetime.strptime(vals['date'], DEFAULT_SERVER_DATE_FORMAT)
        return {
            'type': 'availability',
            'availability': {
                vals['room_type_id']: {
                    date_dt.strftime("%d/%m/%Y"): [
                        vals['avail'],
                        vals['no_ota'],
                        vals['id'],
                    ],
                },
            },
        }

    @api.model
    def send_reservation_notification(self, vals):
        notif = self._generate_reservation_notif(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def send_pricelist_notification(self, vals):
        notif = self._generate_pricelist_notification(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def send_restriction_notification(self, vals):
        notif = self._generate_restriction_notification(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)

    @api.model
    def send_availability_notification(self, vals):
        notif = self._generate_availability_notification(vals)
        self.env['bus.bus'].sendone((self._cr.dbname, 'hotel.reservation',
                                     HOTEL_BUS_CHANNEL_ID), notif)
