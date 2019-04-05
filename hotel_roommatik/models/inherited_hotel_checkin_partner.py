# Copyright 2018 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
from datetime import datetime
import logging

class HotelFolio(models.Model):

    _inherit = 'hotel.checkin.partner'

    @api.model
    def rm_checkin_partner(self, stay):
        # CHECK-IN
        _logger = logging.getLogger(__name__)
        # folio_rm = self.env['hotel.folio'].search([('id', '=', stay['Code'])])
        reservation_rm = self.env['hotel.reservation'].search([('id', '=',
                                                                stay['Code'])])
        # Need checkin?
        total_chekins = reservation_rm.checkin_partner_pending_count
        if total_chekins > 0 and len(stay["Customers"]) <= total_chekins:
            _logger.info('ROOMMATIK checkin %s customer in %s Reservation.',
                         total_chekins,
                         reservation_rm.id)
            for room_partner in stay["Customers"]:
                # ADD costumer ?
                # costumer = self.env['res.partner'].rm_add_customer(room_partner["Customer"])

                # Debug Stop -------------------
                # import wdb; wdb.set_trace()
                # Debug Stop ------------------
                checkin_partner_val = {
                    'folio_id': reservation_rm.folio_id.id,
                    'reservation_id': reservation_rm.id,
                    'enter_date': datetime.strptime(stay["Arrival"],
                                                    "%d%m%Y").date(),
                    'exit_date': datetime.strptime(stay["Departure"],
                                                   "%d%m%Y").date(),
                    'partner_id': room_partner["Customer"]["Id"],
                    'email': room_partner["Customer"]["Contact"]["Email"],
                    'mobile': room_partner["Customer"]["Contact"]["Mobile"],
                    'document_type': room_partner["Customer"][
                                                 "IdentityDocument"]["Type"],
                    'document_number': room_partner["Customer"][
                                                 "IdentityDocument"]["Number"],
                    'document_expedition_date': datetime.strptime(room_partner[
                                            "Customer"]["IdentityDocument"][
                                            "ExpiryDate"], "%d%m%Y").date(),
                    'gender': room_partner["Customer"]["Sex"],
                    'birthdate_date': datetime.strptime(room_partner[
                                    "Customer"]["Birthday"], "%d%m%Y").date(),
                    'code_ine_id': room_partner["Customer"][
                                    "Address"]["Province"],
                    'state': 'booking',
                    }
                try:
                    record = self.env['hotel.checkin.partner'].create(
                                                        checkin_partner_val)
                    _logger.info('ROOMMATIK check-in Document: %s in \
                                                    (%s Reservation) ID:%s.',
                                 checkin_partner_val['document_number'],
                                 checkin_partner_val['reservation_id'],
                                 record.id)
                    stay['Id'] = record.id
                    json_response = stay
                except:
                    json_response = {'Estate': 'Error not create Checkin'}
                    _logger.error('ROOMMATIK writing %s in reservation: %s).',
                                  checkin_partner_val['document_number'],
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
        reserva = self.search([('id', '=', code)])
        stay = {'Code': code}
        stay['Id'] = reserva.folio_id.id
        stay['Room'] = {}
        stay['Room']['Id'] = reserva.reservation_id.room_id.id
        stay['Room']['Name'] = reserva.reservation_id.room_id.name
        stay['RoomType'] =  {}
        stay['RoomType']['Id'] = reserva.reservation_id.room_type_id.id
        stay['RoomType']['Name'] = reserva.reservation_id.room_type_id.name
        stay['RoomType']['GuestNumber'] = "xxxxxxx"
        stay['Arrival'] = reserva.reservation_id.real_checkin + 'T' + reserva.reservation_id.arrival_hour + ':00'
        stay['Departure'] = reserva.reservation_id.real_checkout + 'T' + reserva.reservation_id.departure_hour + ':00'
        # TODO ADD Customers ......................................................checkin_partner_ids
        stay['Customers'] = []
        for idx, cpi in enumerate(reserva.reservation_id.checkin_partner_ids):
            stay['Customers'].append({'Customer':{}})
            stay['Customers'][idx]['Customer']['Id'] = cpi.id
            stay['Customers'][idx]['Customer']['FirstName'] = cpi.partner_id.firstname
            stay['Customers'][idx]['Customer']['LastName1'] = cpi.partner_id.lastname
            stay['Customers'][idx]['Customer']['LastName2'] = cpi.partner_id.lastname2
            stay['Customers'][idx]['Customer']['Birthday'] = cpi.partner_id.birthdate_date
            stay['Customers'][idx]['Customer']['Sex'] = cpi.partner_id.gender
            stay['Customers'][idx]['Customer']['Address'] = {
                                    'Nationality': {},
                                    'Country': cpi.partner_id.country_id.name,
                                    'ZipCode': cpi.partner_id.zip,
                                    'City': cpi.partner_id.city,
                                    'Street': cpi.partner_id.street,
                                    'House': cpi.partner_id.street2,
                                    # 'Flat': "xxxxxxx",
                                    # 'Number': "xxxxxxx",
                                    'Province': cpi.partner_id.state_id.name,
                                    }
            stay['Customers'][idx]['Customer']['IdentityDocument'] = {
                                'Number': cpi.document_number,
                                'Type': cpi.document_type,
                                'ExpiryDate': "",
                                'ExpeditionDate': cpi.document_expedition_date,
                                }

        stay['TimeInterval'] = {}
        stay['TimeInterval']['Id'] = {}
        stay['TimeInterval']['Name'] = {}
        stay['TimeInterval']['Minutes'] = {}
        stay['Adults'] = reserva.reservation_id.adults
        stay['ReservationCode'] = {}
        stay['Total'] = reserva.reservation_id.price_total
        stay['Paid'] = stay['Total'] - reserva.reservation_id.folio_pending_amount
        stay['Outstanding'] = {}
        stay['Taxable'] = reserva.reservation_id.price_tax


        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------

        json_response = json.dumps(stay)

        return json_response
        # return stay

        # stay1 = {
        #
        #     "Id": 123,
        #     "Code": "44",
        #     "Room": {
        #         "Id": 123,
        #         "Name": "Name",
        #     },
        #     "RoomType": {
        #         "Id": 123,
        #         "Name": "Name",
        #         "GuestNumber": 123,
        #     },
        #     "Arrival": date(2001, 7, 19).strftime("%d%m%Y"),
        #     "Departure": date(2001, 7, 19).strftime("%d%m%Y"),
        #     "Customers": {
        #         "Customer": {
        #             "Id": 123,
        #             "FirstName": "FirstName",
        #             "LastName1": "LastName1",
        #             "LastName2": "LastName2",
        #             "Birthday": date(2001, 7, 19).strftime("%d%m%Y"),
        #             "Sex": "Sex",
        #             "Address": {
        #                 "Nationality": "Nationality",
        #                 "Country": "Country",
        #                 "ZipCode": "ZipCode",
        #                 "City": "City",
        #                 "Street": "Street",
        #                 "House": "House",
        #                 "Flat": "Flat",
        #                 "Number": "Number",
        #                 "Province": "Province",
        #                 },
        #             "IdentityDocument": {
        #                 "Number": "Number",
        #                 "Type": "Type",
        #                 "ExpiryDate": date(2001, 7, 19).strftime("%d%m%Y"),
        #                 "ExpeditionDate": date(2001, 7, 19).strftime("%d%m%Y"),
        #                 },
        #             "Contact": {
        #                 "Telephone": "Telephone",
        #                 "Fax": "Fax",
        #                 "Mobile": "Mobile",
        #                 "Email": "Email",
        #                 },
        #             },
        #         "Customer": {
        #             "Id": 124,
        #             "FirstName": "FirstName2",
        #             "LastName1": "LastName12",
        #             "LastName2": "LastName22",
        #             "Birthday": date(2001, 7, 19).strftime("%d%m%Y"),
        #             "Sex": "Sex",
        #             "Address": {
        #                 "Nationality": "Nationality",
        #                 "Country": "Country",
        #                 "ZipCode": "ZipCode",
        #                 "City": "City",
        #                 "Street": "Street",
        #                 "House": "House",
        #                 "Flat": "Flat",
        #                 "Number": "Number",
        #                 "Province": "Province",
        #                 },
        #             "IdentityDocument": {
        #                 "Number": "Number",
        #                 "Type": "Type",
        #                 "ExpiryDate": date(2001, 7, 19).strftime("%d%m%Y"),
        #                 "ExpeditionDate": date(2001, 7, 19).strftime("%d%m%Y"),
        #                 },
        #             "Contact": {
        #                 "Telephone": "Telephone",
        #                 "Fax": "Fax",
        #                 "Mobile": "Mobile",
        #                 "Email": "Email",
        #                 },
        #             },
        #         },
        #     "TimeInterval": {
        #         "Id": 123,
        #         "Name": "Name",
        #         "Minutes": 123,
        #         },
        #     "Adults": 2,
        #     "ReservationCode": "ReservationCode",
        #     "Total": 10.5,
        #     "Paid": 10.5,
        #     "Outstanding": 10.5,
        #     "Taxable": 10.5,
        # }
