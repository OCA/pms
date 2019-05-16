# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Alda Hotels <informatica@aldahotels.com>
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
from openerp import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class HotelCheckinPartner(models.Model):
    _inherit = 'hotel.checkin.partner'

    document_type = fields.Selection(related='partner_id.document_type')
    document_number = fields.Char(related='partner_id.document_number')
    document_expedition_date = fields.Date(
        related='partner_id.document_expedition_date')
    gender = fields.Selection('Gender', related='partner_id.gender')
    birthdate_date = fields.Date('Birhdate',
                                 related='partner_id.birthdate_date')
    code_ine_id = fields.Many2one(related="partner_id.code_ine_id")
    name = fields.Char(related='partner_id.name')
    lastname = fields.Char(related='partner_id.lastname')
    firstname = fields.Char(related='partner_id.firstname')

    @api.model
    def create(self, vals):
        if not vals.get('partner_id'):
            name = self.env['res.partner']._get_computed_name(
                vals.get('lastname'),
                vals.get('firstname')
                )
            partner = self.env['res.partner'].create({
                'name': name,
            })
            vals.update({'partner_id': partner.id})
            vals.pop('firstname')
            vals.pop('lastname')
        return super(HotelCheckinPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        for record in self:
            if not vals.get('partner_id') and not record.partner_id:
                name = self.env['res.partner']._get_computed_name(
                    vals.get('lastname'),
                    vals.get('firstname')
                    )
                partner = self.env['res.partner'].create({
                    'name': name,
                })
                record.update({'partner_id': partner.id})
                vals.pop('firstname')
                vals.pop('lastname')
        return super(HotelCheckinPartner, self).write(vals)

    @api.multi
    def action_on_board(self):
        self.check_required_fields()
        return super(HotelCheckinPartner, self).action_on_board()

    @api.model
    def check_dni(self, dni):
        digits = "TRWAGMYFPDXBNJZSQVHLCKE"
        dig_ext = "XYZ"
        reemp_dig_ext = {'X': '0', 'Y': '1', 'Z': '2'}
        numbers = "1234567890"
        dni = dni.upper()
        if len(dni) == 9:
            dig_control = dni[8]
            dni = dni[:8]
            if dni[0] in dig_ext:
                dni = dni.replace(dni[0], reemp_dig_ext[dni[0]])
            return len(dni) == len([n for n in dni if n in numbers]) \
                and digits[int(dni) % 23] == dig_control
        else:
            return False

    @api.onchange('document_number', 'document_type')
    def onchange_document_number(self):
        for record in self:
            if record.document_type == 'D' and record.document_number:
                if not record.check_dni(record.document_number):
                    record.document_number = False
                    raise UserError(_('Incorrect DNI'))
            if not record.partner_id and record.document_number:
                partner = self.env['res.partner'].search([
                    ('document_number', '=', record.document_number)
                    ], limit=1)
                if partner:
                    record.update({'partner_id': partner})

    @api.multi
    def check_required_fields(self):
        for record in self:
            missing_fields = []
            required_fields = ['document_type', 'document_number',
                               'document_expedition_date', 'gender',
                               'birthdate_date', 'code_ine_id',
                               'lastname', 'firstname']
            for field in required_fields:
                if not record[field]:
                    missing_fields.append(record._fields[field].string)
            if missing_fields:
                raise UserError(
                    _('To perform the checkin the following data are missing:\
                    %s') % (', '.join(missing_fields)))
            if not record.reservation_id.segmentation_ids:
                raise UserError(
                    _('To perform the checkin the segmentation is required'))
