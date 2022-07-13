from odoo import _, fields
from odoo.exceptions import MissingError
from datetime import datetime, timedelta

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAgencyService(Component):
    _inherit = "base.rest.service"
    _name = "pms.price.service"
    _usage = "prices"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.price.search.param"),
        output_param=Datamodel("pms.price.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_prices(self, prices_search_param):
        product = room_type = False
        if prices_search_param.productId:
            product = self.env["product.product"].search([("id", "=", prices_search_param.productId)])
        if prices_search_param.roomTypeId:
            room_type = self.env["pms.room.type"].search([("id", "=", prices_search_param.roomTypeId)])
        if (product and room_type) or (not product and not room_type):
            raise MissingError(_("It is necessary to indicate one and only one product or room type"))
        product = product if product else room_type.product_id

        PmsPriceInfo = self.env.datamodels["pms.price.info"]
        result_prices = []
        date_from = fields.Date.from_string(prices_search_param.dateFrom)
        date_to = fields.Date.from_string(prices_search_param.dateTo)
        dates = [
            date_from + timedelta(days=x)
            for x in range(0, (date_to - date_from).days + 1)
        ]
        for price_date in dates:
            result_prices.append(
                PmsPriceInfo(
                    date=datetime.combine(
                        price_date, datetime.min.time()
                    ).isoformat(),
                    price=round(
                        self._get_product_price(product, prices_search_param, price_date), 2
                    ),
                )
            )
        return result_prices

    def _get_product_price(self, product, price_search_param, date_consumption=False):
        pms_property = self.env["pms.property"].browse(
            price_search_param.pmsPropertyId
        )
        product_context = dict(
            self.env.context,
            date=datetime.today().date(),
            pricelist=price_search_param.pricelistId or False,
            uom=product.uom_id.id,
            fiscal_position=False,
            property=price_search_param.pmsPropertyId,
        )
        if date_consumption:
            product_context["consumption_date"] = date_consumption
        product = product.with_context(product_context)
        return self.env["account.tax"]._fix_tax_included_price_company(
            self.env["product.product"]._pms_get_display_price(
                pricelist_id=price_search_param.pricelistId,
                product=product,
                company_id=pms_property.company_id.id,
                product_qty=price_search_param.productQty or 1,
                partner_id=price_search_param.partnerId or False,
            ),
            product.taxes_id,
            product.taxes_id,  # Not exist service line, we repeat product taxes
            pms_property.company_id,
        )
