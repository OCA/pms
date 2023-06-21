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

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    pay_on_reservation = fields.Boolean("Pay on reservation", default=False)
    pay_on_reservation_method_id = fields.Many2one(
        "pos.payment.method", string="Pay on reservation method"
    )
    reservation_allowed_propertie_ids = fields.Many2many(
        "pms.property", string="Reservation allowed properties"
    )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get("pos_user_force", False):
            return (
                super()
                .sudo()
                .with_context(pos_user_force=False)
                .search_read(domain, fields, offset, limit, order)
            )
        else:
            return super(PosConfig, self).search_read(
                domain, fields, offset, limit, order
            )
