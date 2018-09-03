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
from odoo.addons.hotel import date_utils
from ..components.backend_adapter import DEFAULT_WUBOOK_DATE_FORMAT


class ImportPlanRestrictionsWizard(models.TransientModel):
    _name = 'wubook.wizard.plan.restrictions'

    date_start = fields.Datetime('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)

    @api.multi
    def import_plan_restrictions(self):
        restriction_id = self.env['hotel.room.type.restriction'].browse(
                                            self.env.context.get('active_id'))
        if restriction_id:
            for record in self:
                date_start_dt = date_utils.get_datetime(record.date_start)
                date_end_dt = date_utils.get_datetime(record.date_end)
                if int(restriction_id.wpid) == 0:
                    wres = self.env['wubook'].fetch_rooms_values(
                        date_start_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        date_end_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))
                else:
                    wres = self.env['wubook'].fetch_rplan_restrictions(
                        date_start_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        date_end_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        restriction_id.wpid)
                if not wres:
                    raise ValidationError(_("Can't fetch restrictions \
                                                                from WuBook"))
        return True
