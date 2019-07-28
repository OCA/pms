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
        return {
            'type': 'reservation',
            'action': vals['action'],
            'subtype': vals['type'],
            'title': vals['title'],
            'username': user_id.partner_id.name,
            'userid': user_id.id,
            'reservation': {
                'room_id': vals['room_id'],
                'id': vals['reserv_id'],
                'name': vals['partner_name'],
                'adults': vals['adults'],
                'childer': vals['children'],
                'checkin': vals['checkin'],
                'checkout': vals['checkout'],
                'folio_id': vals['folio_id'],
                'bgcolor': vals['reserve_color'],
                'color': vals['reserve_color_text'],
                'splitted': vals['splitted'],
                'parent_reservation': vals['parent_reservation'],
                'room_name': vals['room_name'],
                'state': vals['state'],
                'only_read': False,
                'fix_days': vals['fix_days'],
                'fix_room': False,
                'overbooking': vals['overbooking'],
                'price_room_services_set': vals['price_room_services_set'],
                'amount_total': vals['pending_amount'] + vals['invoices_paid'],
                'real_dates': vals['real_dates'],
                'channel_type': vals['channel_type'],
            },
            'tooltip': {
                'folio_name': vals['folio_name'],
                'name': vals['partner_name'],
                'phone': vals['partner_phone'],
                'email': vals['partner_email'],
                'room_type_name': vals['room_type_name'],
                'adults': vals['adults'],
                'children': vals['children'],
                'checkin': vals['checkin'],
                'checkout': vals['checkout'],
                'arrival_hour': vals['arrival_hour'],
                'departure_hour': vals['departure_hour'],
                'price_room_services_set': vals['price_room_services_set'],
                'invoices_paid': vals['invoices_paid'],
                'pending_amount': vals['pending_amount'],
                'type': vals['reservation_type'],
                'closure_reason': vals['closure_reason'],
                'out_service_description': vals['out_service_description'],
                'splitted': vals['splitted'],
                'real_dates': vals['real_dates'],
                'channel_type': vals['channel_type'],
                'board_service_name': vals['board_service_name'],
                'services': vals['services'],
            }
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
                vals['room_type_id']: {
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
