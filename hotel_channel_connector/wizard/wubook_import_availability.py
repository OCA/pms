# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
from openerp.exceptions import ValidationError
from openerp import models, fields, api, _
from ..components.backend_adapter import DEFAULT_WUBOOK_DATE_FORMAT


class ImportAvailabilityWizard(models.TransientModel):
    _name = 'wubook.wizard.availability'

    date_start = fields.Datetime('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)
    set_max_avail = fields.Boolean('Set max avail?', default=True)

    @api.multi
    def import_availability(self):
        for record in self:
            wres = self.env['wubook'].fetch_rooms_values(
                record.date_start,
                record.date_end,
                set_max_avail=record.set_max_avail)
            if not wres:
                raise ValidationError(_("Can't fetch availability from WuBook"))
        return True
