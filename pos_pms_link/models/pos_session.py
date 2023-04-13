##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2023 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import json
from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _accumulate_amounts(self, data):
        res = super(PosSession, self)._accumulate_amounts(data)
        if self.config_id.pay_on_reservation and self.config_id.pay_on_reservation_method_id:
            reservation_orders = self.order_ids.filtered(lambda x: x.pms_reservation_id)
            reservation_taxes = sum([order.amount_tax for order in reservation_orders])
            reservation_no_taxes = sum([order.amount_total - order.amount_tax for order in reservation_orders])

            for element, value in dict(res["taxes"]).items():
                value['amount'] = value['amount'] + reservation_taxes
                value['amount_converted'] = value['amount_converted'] + reservation_taxes
                value['base_amount'] = value['base_amount'] + reservation_no_taxes
                value['base_amount_converted'] = value['base_amount_converted'] + reservation_no_taxes
            
            for element, value in dict(res["sales"]).items():
                value['amount'] = value['amount'] - reservation_no_taxes
                value['amount_converted'] = value['amount_converted'] - reservation_no_taxes
            
            if self.config_id.pay_on_reservation_method_id.split_transactions:
                for element, value in dict(res["split_receivables"]).items():
                    if element.payment_method_id == self.config_id.pay_on_reservation_method_id:
                        value['amount'] = 0.0
                        value['amount_converted'] = 0.0
            
            else:
                for element, value in dict(res["combine_receivables"]).items():
                    if element == self.config_id.pay_on_reservation_method_id:
                        value['amount'] = 0.0
                        value['amount_converted'] = 0.0
        return res