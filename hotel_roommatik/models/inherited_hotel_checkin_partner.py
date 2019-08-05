# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
from odoo.addons.hotel_roommatik.models.roommatik import (
    DEFAULT_ROOMMATIK_DATE_FORMAT,
    DEFAULT_ROOMMATIK_DATETIME_FORMAT)
from datetime import datetime
import logging


class HotelFolio(models.Model):

    _inherit = 'hotel.checkin.partner'

    @api.model
    def rm_checkin_partner(self, stay):
        _logger = logging.getLogger(__name__)
        if not stay.get('ReservationCode'):
            reservation_obj = self.env['hotel.reservation']
            vals = {
                'checkin': stay["Arrival"],
                'checkout': stay["Departure"],
                'adults': stay['Adults'],
                'arrival_hour': stay['Arrival_hour'],
                'room_type_id': stay['RoomType']['Id'],
                'partner_id': stay["Customers"][0]["Id"],
                'segmentation_ids': (6, 0, stay['Segmentation']),
                'channel_type': 'virtualdoor',
            }
            reservation_rm = reservation_obj.create(vals)
        else:
            reservation_rm = self.env['hotel.reservation'].browse(
                stay['ReservationCode'])
        total_chekins = reservation_rm.checkin_partner_pending_count
        if total_chekins > 0 and len(stay["Customers"]) <= total_chekins:
            _logger.info('ROOMMATIK checkin %s customer in %s Reservation.',
                         total_chekins,
                         reservation_rm.id)
            for room_partner in stay["Customers"]:
                if room_partner['Address']['Nationality'] == 'ESP':
                    code_ine = room_partner['Address']['Province']
                else:
                    code_ine = room_partner['Address']['Nationality']
                province = self.env['code.ine'].search(
                    [('name', '=', code_ine)], limit=1)
                code_ine = province.id

                checkin_partner_val = {
                    'folio_id': reservation_rm.folio_id.id,
                    'reservation_id': reservation_rm.id,
                    'partner_id': room_partner["Id"],
                    'enter_date': stay["Arrival"],
                    'exit_date': stay["Departure"],
                    'code_ine_id': code_ine,
                    }
                try:
                    record = self.env['hotel.checkin.partner'].create(
                        checkin_partner_val)
                    _logger.info('ROOMMATIK check-in partner: %s in \
                                                    (%s Reservation) ID:%s.',
                                 checkin_partner_val['partner_id'],
                                 checkin_partner_val['reservation_id'],
                                 record.id)
                    record.action_on_board()
                    stay['Id'] = record.id
                    stay['Room'] = reservation_rm.room_id.id
                    json_response = stay
                except Exception as e:
                    error_name = 'Error not create Checkin '
                    error_name += e.name
                    json_response = {'Estate': error_name}
                    _logger.error('ROOMMATIK writing %s in reservation: %s).',
                                  checkin_partner_val['partner_id'],
                                  checkin_partner_val['reservation_id'])
                    return json_response

        else:
            json_response = {'Estate': 'Error checkin_partner_pending_count \
                                                        values do not match.'}
            _logger.error('ROOMMATIK checkin pending count do not match for \
                                        Reservation ID %s.', reservation_rm.id)
        json_response = json.dumps(json_response)
        return json_response

    @api.model
    def rm_get_stay(self, code):
        # BUSQUEDA POR LOCALIZADOR
        checkin_partner = self.search([('id', '=', code)])
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')
        if any(checkin_partner):
            arrival = "%s %s:00" % (checkin_partner.enter_date.strftime(
                DEFAULT_ROOMMATIK_DATE_FORMAT), default_arrival_hour)
            departure = "%s %s:00" % (checkin_partner.exit_date.strftime(
                DEFAULT_ROOMMATIK_DATE_FORMAT), default_departure_hour)
            stay = {'Code': checkin_partner.id}
            stay['Id'] = checkin_partner.id
            stay['Room'] = {}
            stay['Room']['Id'] = checkin_partner.reservation_id.room_id.id
            stay['Room']['Name'] = checkin_partner.reservation_id.room_id.name
            stay['RoomType'] = {}
            stay['RoomType']['Id'] = checkin_partner.reservation_id.room_type_id.id
            stay['RoomType']['Name'] = checkin_partner.reservation_id.room_type_id.name
            stay['Arrival'] = arrival
            stay['Departure'] = departure
            stay['Customers'] = []
            for idx, cpi in enumerate(checkin_partner.reservation_id.checkin_partner_ids):
                stay['Customers'].append({'Customer': {}})
                stay['Customers'][idx]['Customer'] = self.env[
                    'res.partner'].rm_get_a_customer(cpi.partner_id.id)
            stay['TimeInterval'] = {}
            stay['TimeInterval']['Id'] = {}
            stay['TimeInterval']['Name'] = {}
            stay['TimeInterval']['Minutes'] = {}
            stay['Adults'] = checkin_partner.reservation_id.adults
            stay['ReservationCode'] = {}
            stay['Total'] = checkin_partner.reservation_id.price_total
            stay['Paid'] = checkin_partner.reservation_id.folio_id.invoices_paid
            stay['Outstanding'] = checkin_partner.reservation_id.folio_id.pending_amount
            stay['Taxable'] = checkin_partner.reservation_id.price_tax

        else:
            stay = {'Code': ""}

        json_response = json.dumps(stay)
        return json_response
