# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
from datetime import datetime
import logging


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def rm_add_customer(self, customer):
        # RoomMatik API CREACIÓN DE CLIENTE
        _logger = logging.getLogger(__name__)

        partner_res = self.env['res.partner'].search([(
            'document_number', '=',
            customer['IdentityDocument']['Number'])])

        json_response = {'Id': 0}
        if any(partner_res):
            # Change customer data
            _logger.warning('ROOMMATIK %s exist in BD [ %s ] Rewriting',
                            partner_res[0].document_number,
                            partner_res[0].id,)
            try:
                partner_res[0].update(self.rm_prepare_customer(customer))
                write_custumer = partner_res[0]
            except:
                _logger.error('ROOMMATIK Rewriting [%s] in BD [ %s ] ID',
                              partner_res[0].document_number,
                              partner_res[0].id,)
        else:
            # Create new customer
            try:
                write_custumer = self.create(self.rm_prepare_customer(customer))
                _logger.info('ROOMMATIK Writing %s Name: %s',
                             customer['IdentityDocument']['Number'],
                             customer['FirstName'])
            except:
                _logger.error('ROOMMATIK Creating %s %s in BD',
                              customer['IdentityDocument']['Number'],
                              customer['FirstName'])
        json_response = self.rm_get_a_customer(write_custumer.id)
        json_response = json.dumps(json_response)
        return json_response

    def rm_prepare_customer(self, customer):
        # Check Sex string
        if customer['Sex'] not in {'male', 'female'}:
            customer['Sex'] = ''
        # Check state_id
        city_srch = self.env['res.country.state'].search([
            ('name', 'ilike', customer['Address']['Province'])])
        country = self.env['res.country'].search([
            ('name', 'ilike', customer['Address']['Province'])])
        # Create Street2s
        street_2 = customer['Address']['House']
        street_2 += ' ' + customer['Address']['Flat']
        street_2 += ' ' + customer['Address']['Number']
        metadata = {
            'firstname': customer['FirstName'],
            'lastname': customer['LastName1'],
            'lastname2': customer['LastName2'],
            'birthdate_date': datetime.strptime(customer['Birthday'],
                                                "%d%m%Y").date(),
            'gender': customer['Sex'],
            'zip': customer['Address']['ZipCode'],
            'city': customer['Address']['City'],
            'street': customer['Address']['Street'],
            'street2': street_2,
            'state_id': city_srch.id,
            'phone': customer['Contact']['Telephone'],
            'mobile': customer['Contact']['Mobile'],
            'email': customer['Contact']['Email'],
            'document_number': customer['IdentityDocument']['Number'],
            'document_type': customer['IdentityDocument']['Type'],
            'document_expedition_date': datetime.strptime(customer[
                'IdentityDocument']['ExpeditionDate'],
                "%d%m%Y").date(),
            }
        return {k: v for k, v in metadata.items() if v is not ""}

    def rm_get_a_customer(self, customer):
        # Prepare a Customer for RoomMatik
        partner = self.search([('id', '=', customer)])
        response = {}
        response['Id'] = partner.id
        response['FirstName'] = partner.firstname
        response['LastName1'] = partner.lastname
        response['LastName2'] = partner.lastname2
        response['Birthday'] = partner.birthdate_date
        response['Sex'] = partner.gender
        response['Address'] = {'Nationality': {},
                               'Country': partner.country_id.name,
                               'ZipCode': partner.zip,
                               'City': partner.city,
                               'Street': partner.street,
                               'House': partner.street2,
                               # 'Flat': "xxxxxxx",
                               # 'Number': "xxxxxxx",
                               'Province': partner.state_id.name,
                               }
        response['IdentityDocument'] = {
                            'Number': partner.document_number,
                            'Type': partner.document_type,
                            'ExpiryDate': "",
                            'ExpeditionDate': partner.document_expedition_date,
                            }
        response['Contact'] = {
                                'Telephone': partner.phone,
                                # 'Fax': 'xxxxxxx',
                                'Mobile': partner.mobile,
                                'Email': partner.email,
                                }
        return response
