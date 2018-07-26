# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <alex@aloxa.eu>
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
from odoo import models, fields, api


class VirtualRoomRestriction(models.Model):
    _name = 'hotel.virtual.room.restriction'

    name = fields.Char('Restriction Plan Name', required=True)
    item_ids = fields.One2many('hotel.virtual.room.restriction.item',
                               'restriction_id', string='Restriction Items',
                               copy=True)
    active = fields.Boolean('Active',
                            help='If unchecked, it will allow you to hide the \
                                    restriction plan without removing it.',
                            default=True)

    @api.multi
    @api.depends('name')
    def name_get(self):
        restriction_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_restrictions_id')
        if restriction_id:
            restriction_id = int(restriction_id)
        names = []
        for record in self:
            if record.id == restriction_id:
                names.append((record.id, '%s (Parity)' % record.name))
            else:
                names.append((record.id, record.name))
        return names
