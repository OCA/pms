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
from openerp import models, api, _


class MassiveChangesWizard(models.TransientModel):
    _inherit = 'hotel.wizard.duplicate.reservation'

    @api.multi
    def duplicate_reservation(self):
        reservation_id = self.env['hotel.reservation'].browse(
            self.env.context.get('active_id'))
        if reservation_id and reservation_id.is_from_ota:
            raise ValidationError(_("Can't duplicate a reservation from channel"))
        return super(MassiveChangesWizard, self).duplicate_reservation()
