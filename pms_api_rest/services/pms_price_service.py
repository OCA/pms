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
        product = room_type = board_service = False
        if prices_search_param.roomTypeId:
            room_type = self.env["pms.room.type"].search([("id", "=", prices_search_param.roomTypeId)])
        if prices_search_param.productId:
            product = self.env["product.product"].search([("id", "=", prices_search_param.productId)])
        if prices_search_param.boardServiceId:
            board_service = self.env["pms.board.service.room.type"].search([
                ("id", "=", prices_search_param.boardServiceId)]
            )
        if sum([var is not False for var in [product, room_type, board_service]]) != 1:
            raise MissingError(_("It is necessary to indicate one and only one product, board service or room type"))

        PmsPriceInfo = self.env.datamodels["pms.price.info"]
        result_prices = []
        date_from = fields.Date.from_string(prices_search_param.dateFrom)
        date_to = fields.Date.from_string(prices_search_param.dateTo)
        dates = [
            date_from + timedelta(days=x)
            for x in range(0, (date_to - date_from).days + 1)
        ]
        for price_date in dates:
            if board_service:
                result_prices.append(
                    PmsPriceInfo(
                        date=datetime.combine(
                            price_date, datetime.min.time()
                        ).isoformat(),
                        price=round(
                            self._get_board_service_price(
                                board_service=board_service,
                                pms_property_id=prices_search_param.pmsPropertyId,
                                pricelist_id=prices_search_param.pricelistId,
                                partner_id=prices_search_param.partnerId,
                                product_qty=prices_search_param.productQty,
                                date_consumption=price_date
                            ), 2
                        ),
                    )
                )
            else:
                result_prices.append(
                    PmsPriceInfo(
                        date=datetime.combine(
                            price_date, datetime.min.time()
                        ).isoformat(),
                        price=round(
                            self._get_product_price(
                                product=product if product else room_type.product_id,
                                pms_property_id=prices_search_param.pmsPropertyId,
                                pricelist_id=prices_search_param.pricelistId,
                                partner_id=prices_search_param.partnerId,
                                product_qty=prices_search_param.productQty,
                                date_consumption=price_date
                            ), 2
                        ),
                    )
                )
        return result_prices

    def _get_product_price(
        self,
        product,
        pms_property_id,
        pricelist_id=False,
        partner_id=False,
        product_qty=False,
        date_consumption=False,
        board_service_id=False,
    ):
        pms_property = self.env["pms.property"].browse(
            pms_property_id
        )
        product_context = dict(
            self.env.context,
            date=datetime.today().date(),
            pricelist=pricelist_id,
            uom=product.uom_id.id,
            fiscal_position=False,
            property=pms_property_id,
        )
        if date_consumption:
            product_context["consumption_date"] = date_consumption
        if board_service_id:
            product_context["board_service"] = board_service_id
        product = product.with_context(product_context)
        return self.env["account.tax"]._fix_tax_included_price_company(
            self.env["product.product"]._pms_get_display_price(
                pricelist_id=pricelist_id,
                product=product,
                company_id=pms_property.company_id.id,
                product_qty=product_qty or 1,
                partner_id=partner_id,
            ),
            product.taxes_id,
            product.taxes_id,  # Not exist service line, we repeat product taxes
            pms_property.company_id,
        )

    def _get_board_service_price(
        self,
        board_service,
        pms_property_id,
        pricelist_id=False,
        partner_id=False,
        product_qty=False,
        date_consumption=False,
    ):
        price = 0
        for product in board_service.board_service_line_ids.mapped("product_id"):
            price += self._get_product_price(
                product=product,
                pms_property_id=pms_property_id,
                pricelist_id=pricelist_id,
                partner_id=partner_id,
                product_qty=product_qty,
                date_consumption=date_consumption,
            )
        return price
