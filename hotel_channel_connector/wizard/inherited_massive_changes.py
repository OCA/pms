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
from datetime import datetime, timedelta
from openerp.exceptions import ValidationError
from openerp import models, api


class MassiveChangesWizard(models.TransientModel):
    _inherit = 'hotel.wizard.massive.changes'

    @api.model
    def _get_availability_values(self, ndate, vroom, record):
        vals = super(MassiveChangesWizard, self)._get_availability_values(
            ndate, vroom, record)
        vals.update({
            'wmax_avail': vals['avail']
        })
        return vals

    @api.multi
    def massive_change(self):
        res = super(MassiveChangesWizard, self).massive_change()
        self.env['wubook'].push_changes()
        return res
