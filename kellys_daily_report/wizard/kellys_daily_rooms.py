# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2019 Jose Luis Algara Toledo <osotranquilo@gmail.com>
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
from odoo import fields, models


class KellysRooms(models.TransientModel):
    _name = 'kellysrooms'

    habitacion = fields.Char('Habitacion')
    habitacionid = fields.Integer('Habitacion ID')
    tipo = fields.Selection([(1, 'Salida'), (2, 'Cliente'), (3, 'Revisar'),
                            (4, 'Staff'), (5, 'Averia')],
                            string='Limpiar como')
    notas = fields.Char('Notas limpieza')
    checkin = fields.Char('Entrada')
    checkout = fields.Char('Salida')
    kelly = fields.Many2one('kellysnames', string='Asignado a:')
    clean_date = fields.Date('Clean Date')
