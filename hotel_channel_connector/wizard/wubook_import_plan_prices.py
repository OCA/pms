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


class ImportPlanPricesWizard(models.TransientModel):
    _name = 'wubook.wizard.plan.prices'

    date_start = fields.Datetime('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)

    @api.multi
    def import_plan_prices(self):
        pricelist_id = self.env['product.pricelist'].browse(
                                            self.env.context.get('active_id'))
        if pricelist_id:
            for record in self:
                date_start_dt = fields.Date.from_string(record.date_start)
                date_end_dt = fields.Date.from_string(record.date_end)
                wres = self.env['wubook'].fetch_plan_prices(
                    pricelist_id.wpid,
                    date_start_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    date_end_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))
                if not wres:
                    raise ValidationError(_("Can't fetch plan prices \
                                                                from WuBook"))
        return True
