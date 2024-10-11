##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2022 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
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
from odoo import api, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

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
            return super(ProductPricelist, self).search_read(
                domain, fields, offset, limit, order
            )


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

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
            return super(ProductPricelistItem, self).search_read(
                domain, fields, offset, limit, order
            )
