# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Alda Hotels <informatica@aldahotels.com>
#                       Jose Luis Algara <osotranquilo@gmail.com>
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
from openerp.exceptions import UserError
from openerp.tools.translate import _
from datetime import datetime, timedelta

class CheckinWizard(models.TransientModel):
    _inherit = 'checkin.wizard'

    def validation_under_age(self):
        if self.birthdate_date_cardex != False:
            years = str(datetime.now().date() - timedelta(days=365*16+4))
            limit_date = datetime.strptime(years, "%Y-%m-%d")
            birth_date = datetime.strptime(self.birthdate_date_cardex, '%Y-%m-%d')
            limit = str(limit_date.day)+ ' de ' +  str(limit_date.month)+ ' de ' + str(limit_date.year)
            if limit_date < birth_date:
                return {'warning': {'title': _('Error in Birthdate'), 'message': _('Does the client have less than 16 years?. Data collection is not performed for those born before %s.' % (limit)),},}
            if self.polexpedition_cardex != False:
                if self.birthdate_date_cardex > self.polexpedition_cardex:
                    raise ValidationError(_('Date of document shipment, prior to birth date'))

    @api.onchange('polexpedition_cardex')
    def validation_polexpedition(self):
        if self.birthdate_date_cardex != False and self.polexpedition_cardex != False:
            if self.birthdate_date_cardex > self.polexpedition_cardex:
                return {'warning': {'title': _('Error in Birthdate or Expedition date'), 'message': _('Date of document shipment, prior to birth date'),},}

    # Validation for DNI/Permiso conducir erroneo
    @api.onchange('poldocument_cardex', 'documenttype_cardex')
    def validation_poldocument_dni(self):
        if self.poldocument_cardex != False:
            if self.documenttype_cardex in ['D','C']:
                validcaracter = "TRWAGMYFPDXBNJZSQVHLCKE"
                dig_ext = "XYZ"
                reemp_dig_ext = {'X':'0', 'Y':'1', 'Z':'2'}
                numeros = "1234567890"
                dni = self.poldocument_cardex.upper()
                if len(dni) == 9:
                    dig_control = dni[8]
                    dni = dni[:8]
                    # 'extranjero empieza por XYZ'
                    if dni[0] in dig_ext:
                        dni = dni.replace(dni[0], reemp_dig_ext[dni[0]])
                    if not ((len(dni) == len([n for n in dni if n in numeros])) and (validcaracter[int(dni)%23] == dig_control)):
                        return {'warning': {'title': _('Error in DNI/NIE/DRIVE LICENSE'), 'message': _('Wrong DNI/NIE/DRIVE LICENSE, check it.'),},}
                else:
                    return {'warning': {'title': _('Error in DNI/NIE/DRIVE LICENSE'), 'message': _('DNI/NIE/DRIVE LICENSE erroneous length, the correct format is: (12345678A or X1234567A)'),},}

    # Validation for Tipo de documento no valido para Extranjero
    # @api.onchange('x')
    # Pendiente

    # Validation for Nacionalidad erronea
    # @api.onchange('x')
    # Pendiente

    # NOTE: All the fields are required but they are set required=True in the .xml
    # The reason is found in the bt_select_partner and bt_create_partner buttons to bypass the ORM null constraint
    # when the buttons are clicked to show the hidden fields

    documenttype_cardex = fields.Selection([
        ('D', 'DNI'),
        ('P', 'Pasaporte'),
        ('C', 'Permiso de Conducir'),
        ('I', 'Carta o Doc. de Identidad'),
        ('N', 'Permiso Residencia Español'),
        ('X', 'Permiso Residencia Europeo')],
        help='Select a valid document type',
        default='D',
        string='Doc. type')

    poldocument_cardex = fields.Char('Doc. number')

    polexpedition_cardex = fields.Date('Expedition date')

    gender_cardex = fields.Selection([('male', 'Male'), ('female', 'Female')])

    birthdate_date_cardex = fields.Date("Birthdate")

    code_ine_cardex = fields.Many2one('code_ine',
            help='Country or province of origin. Used for INE statistics.')

    # TODO: Add tags in the cardex not in the partner anb move this field to out of localization
    #category_id_cardex = fields.Many2many('res.partner.category', 'id', required=True)

    @api.multi
    def pdf_viajero(self, cardex_id):
        cardex = self.env['cardex'].search([('id', '=', cardex_id)])
        return self.env['report'].get_action(cardex, 'report.viajero')

    @api.multi
    def action_save_check(self):
        # Check dates
        self.validation_under_age()
        # take a 'snapshot' of the current cardexes in this reservation
        record_id = self.env['hotel.reservation'].browse(self.reservation_id.id)
        old_cardex = self.env['cardex'].search([('reservation_id', '=', record_id.id)])

        # the above lines must be executed before call the super().action_save_check()

        # call the super action_save_check() for checkin
        super(Wizard, self).action_save_check()

        # prepare category in partner from category_id
        the_list = self.segmentation_id - self.partner_id.category_id
        the_list = self.partner_id.category_id + the_list

        # prepare localization partner values
        partner_vals = {
            'documenttype': self.documenttype_cardex,
            'poldocument': self.poldocument_cardex,
            'polexpedition': self.polexpedition_cardex,
            'gender': self.gender_cardex,
            'birthdate_date': self.birthdate_date_cardex,
            # (4, ID) link to existing record with id = ID (adds a relationship) ...
            'code_ine': self.code_ine_cardex.id,
            # (6, 0, [IDs]) replace the list of linked IDs ...
            'category_id': [(6, False, [x.id for x in the_list])],
        }

        # Update Accounting VAT number on customer
        if self.documenttype_cardex in ('D','C'):
                partner_vat = 'ES' + self.poldocument_cardex
                partner_vals.update({
                    'vat': partner_vat
                    })

        # Are you templed to merge the following write with the super() ?
        # Be warned: Premature optimization is the root of all evil -- DonaldKnuth
        # This TransientModel inherit from checkin.wizard and it is intended for localization
        # So, if you need to write something here must be _after_ the super()

        # update the localization partner values for this reservation
        self.partner_id.sudo().write(partner_vals);

        # get the last cardex in this reservation (set difference theory)
        cardex = self.env['cardex'].search([('reservation_id', '=', record_id.id)]) - old_cardex
        return self.pdf_viajero(cardex.id)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        # call the super update_partner_fields
        super(Wizard, self).onchange_partner_id()
        # update local fields
        self.documenttype_cardex = self.partner_id.documenttype;
        self.poldocument_cardex = self.partner_id.poldocument;
        self.polexpedition_cardex = self.partner_id.polexpedition;
        self.gender_cardex = self.partner_id.gender;
        self.birthdate_date_cardex = self.partner_id.birthdate_date;
        self.code_ine_cardex = self.partner_id.code_ine;
        #self.category_id_cardex = self.partner_id.category_id;
