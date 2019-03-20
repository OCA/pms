# Copyright 2018 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import _, api, fields, models
from datetime import datetime


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def rm_add_customer(self, customer):
        # CREACIÓN DE CLIENTE
        partnername = customer['LastName1'] + ' ' + customer['LastName2'] + ' ' + customer['FirstName']
        partner_res = self.env['res.partner'].search(
            [('name', '=', partnername)])
        # Need a smart search function here (Check name, document, mail) return unique or null customer.

        json_response = dict()
        if any(partner_res):
            json_response = {
                "Id": partner_res.id,
                "FirstName": partner_res.firstname,
                "LastName1": partner_res.lastname,
                "LastName2": partner_res.lastname2,
                "Birthday": partner_res.birthdate_date,
                "Sex": partner_res.gender,
                "IdentityDocument": [{
                    "Number": "Null",
                    "Type": "Null",
                    "ExpiryDate": "dateTime",
                    "ExpeditionDate": "dateTime",
                    "Address": [{
                        "Nationality": "Null",
                        "Country": partner_res.country_id.name,
                        "ZipCode": partner_res.zip,
                        "City": partner_res.city,
                        "Street": partner_res.street,
                        "House": "Null",
                        "Flat": "Null",
                        "Number": "Null",
                        "Province": partner_res.state_id.name,
                    }],
                }],
                "Contact": [{
                    "Telephone": partner_res.phone,
                    "Fax": "Null",
                    "Mobile": partner_res.mobile,
                    "Email": partner_res.email,
                }]
            }
        else:
            # Create new customer
            json_response = {'Id': 0}

            # Check Sex string
            if customer['Sex'] not in {'male', 'female'}:
                customer['Sex'] = ''

            # Check state_id
            city_srch = self.env['res.country.state'].search([
                ('name', 'ilike',
                    customer['IdentityDocument'][0]['Address'][0]['Province'])])

            # Create Street2
            street_2 = 'Nº ' + customer['IdentityDocument'][0]['Address'][0]['House']
            street_2 += ', ' + customer['IdentityDocument'][0]['Address'][0]['Flat']
            street_2 += ', ' + customer['IdentityDocument'][0]['Address'][0]['Number']

            # Debug Stop -------------------
            #import wdb; wdb.set_trace()
            # Debug Stop -------

            # Check birthdate_date
            # Here need to convert birthdate_date to '%d%m%Y' fomat

            write_custumer = self.create({
                'firstname': customer['FirstName'],
                'lastname': customer['LastName1'],
                'lastname2': customer['LastName2'],
                'birthdate_date': datetime.strptime(
                    customer['Birthday'], '%d%m%Y'),
                'gender': customer['Sex'],
                'zip': customer['IdentityDocument'][0]['Address'][0]['ZipCode'],
                'city': customer['IdentityDocument'][0]['Address'][0]['City'],
                'street': customer['IdentityDocument'][0]['Address'][0]['Street'],
                'street2': street_2,
                'state_id': city_srch.id,
                'phone': customer['Contact'][0]['Telephone'],
                'mobile': customer['Contact'][0]['Mobile'],
                'email': customer['Contact'][0]['Email'],
                })


            json_response = {'Id': write_custumer.id}

        # Id: será 0 en la solicitud y será diferente de 0 si el cliente se ha creado
        # correctamente en el PMS.
        # FirstName: nombre.
        # LastName1: primer apellido.
        # LastName2: segundo apellido.
        # Birthday: fecha de nacimiento.
        # Sex: sexo. Puede ser “M” para masculino o “F” para femenino.
        # IdentityDocument: documento de identidad, formado por los siguientes
        # valores:
        # o Number: número de documento.
        # o Type: tipo de documento. Puede ser:
        # ▪ C: permiso de conducir.
        # ▪ X: permiso de residencia europeo.
        # ▪ D: DNI.
        # ▪ I: documento de identidad.
        # ▪ P: pasaporte.
        # ▪ N: permiso de residencia español.
        # o Expedition: fecha de expedición.
        # o Expiration: fecha de caducidad.
        # Address: dirección, formada por los siguientes valores:
        # o City: ciudad.
        # o Country: país (código ISO 3).
        # o Flat: piso.
        # o Nationality: nacionalidad (código ISO 3).
        # o Number: número.
        # o StateOrProvince: estado o provincia.
        # o Street: calle.
        # o ZipCode: código postal.

        json_response = json.dumps(json_response)

        return json_response
