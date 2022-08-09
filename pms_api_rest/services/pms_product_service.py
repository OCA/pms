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
                    perDay=product.per_day,
                    perPerson=product.per_person,
                    consumedOn=product.consumed_on,
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
                perDay=product.per_day,
                perPerson=product.per_person,
            )
        else:
            raise MissingError(_("Product not found"))
