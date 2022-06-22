from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsProductService(Component):
    _inherit = "base.rest.service"
    _name = "pms.product.service"
    _usage = "products"
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
        input_param=Datamodel("pms.product.search.param"),
        output_param=Datamodel("pms.product.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_products(self, product_search_param):
        domain = [("sale_ok", "=", True)]
        if product_search_param.name:
            domain.append(("name", "like", product_search_param.name))
        if product_search_param.ids:
            domain.append(("id", "in", product_search_param.ids))
        if product_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    (
                        "pms_property_ids",
                        "in",
                        product_search_param.pmsPropertyId,
                    ),
                    ("pms_property_ids", "=", False),
                ]
            )
        result_products = []
        PmsProductInfo = self.env.datamodels["pms.product.info"]
        for product in self.env["product.product"].search(
            domain,
        ):
            result_products.append(
                PmsProductInfo(
                    id=product.id,
                    name=product.name,
                    price=self._get_product_price(product, product_search_param),
                    perDay=product.per_day,
                    perPerson=product.per_person,
                )
            )
        return result_products

    @restapi.method(
        [
            (
                [
                    "/<int:product_id>",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.product.search.param"),
        output_param=Datamodel("pms.product.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_product(self, product_id, product_search_param):
        product = self.env["product.product"].browse(product_id)
        if product and product.sale_ok:
            PmsProductInfo = self.env.datamodels["pms.product.info"]
            return PmsProductInfo(
                id=product.id,
                name=product.name,
                price=self._get_product_price(product, product_search_param),
                perDay=product.per_day,
                perPerson=product.per_person,
            )
        else:
            raise MissingError(_("Product not found"))

    def _get_product_price(self, product, product_search_param):
        pms_property = self.env["pms.property"].browse(
            product_search_param.pmsPropertyId
        )
        product_context = dict(
            self.env.context,
            date=datetime.today().date(),
            pricelist=product_search_param.pricelistId or False,
            uom=product.uom_id.id,
            fiscal_position=False,
            property=product_search_param.pmsPropertyId,
        )
        if product_search_param.dateConsumption:
            product_context["consumption_date"] = product_search_param.dateConsumption
        product = product.with_context(product_context)
        return self.env["account.tax"]._fix_tax_included_price_company(
            self.env["product.product"]._pms_get_display_price(
                pricelist_id=product_search_param.pricelistId,
                product=product,
                company_id=pms_property.company_id.id,
                product_qty=product_search_param.productQty or 1,
                partner_id=product_search_param.partnerId,
            ),
            product.taxes_id,
            product.taxes_id,  # Not exist service line, we repeat product taxes
            pms_property.company_id,
        )
