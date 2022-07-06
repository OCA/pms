import re
from datetime import datetime, timedelta

from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPricelistService(Component):
    _inherit = "base.rest.service"
    _name = "pms.pricelist.service"
    _usage = "pricelists"
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
        input_param=Datamodel("pms.search.param", is_list=False),
        output_param=Datamodel("pms.pricelist.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_pricelists(self, pms_search_param, **args):

        pricelists_all_properties = self.env["product.pricelist"].search(
            [("pms_property_ids", "=", False)]
        )
        if pms_search_param.pmsPropertyIds:
            pricelists = set()
            for index, prop in enumerate(pms_search_param.pmsPropertyIds):
                pricelists_with_query_property = self.env["product.pricelist"].search(
                    [("pms_property_ids", "=", prop)]
                )
                if index == 0:
                    pricelists = set(pricelists_with_query_property.ids)
                else:
                    pricelists = pricelists.intersection(
                        set(pricelists_with_query_property.ids)
                    )
            pricelists_total = list(
                set(list(pricelists) + pricelists_all_properties.ids)
            )
        else:
            pricelists_total = list(pricelists_all_properties.ids)
        domain = [
            ("id", "in", pricelists_total),
        ]

        PmsPricelistInfo = self.env.datamodels["pms.pricelist.info"]
        result_pricelists = []
        for pricelist in self.env["product.pricelist"].search(domain):
            result_pricelists.append(
                PmsPricelistInfo(
                    id=pricelist.id,
                    name=pricelist.name,
                    pmsPropertyIds=pricelist.pms_property_ids.mapped("id"),
                )
            )
        return result_pricelists

    @restapi.method(
        [
            (
                [
                    "/<int:pricelist_id>/pricelist-items",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.pricelist.item.search.param", is_list=False),
        output_param=Datamodel("pms.pricelist.item.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_pricelists_items(self, pricelist_id, pricelist_item_search_param):
        result = []
        record_pricelist_id = self.env["product.pricelist"].search(
            [("id", "=", pricelist_id)]
        )
        if not record_pricelist_id:
            raise MissingError
        PmsPricelistItemInfo = self.env.datamodels["pms.pricelist.item.info"]
        rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", pricelist_item_search_param.pmsPropertyId)]
        )
        date_from = datetime.strptime(
            pricelist_item_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            pricelist_item_search_param.dateTo, "%Y-%m-%d"
        ).date()

        for date in (
            date_from + timedelta(d) for d in range((date_to - date_from).days + 1)
        ):
            for room_type in self.env["pms.room.type"].search(
                [("id", "in", rooms.mapped("room_type_id").ids)]
            ):
                item = self.env["product.pricelist.item"].search(
                    [
                        ("pricelist_id", "=", pricelist_id),
                        ("applied_on", "=", "0_product_variant"),
                        ("product_id", "=", room_type.product_id.id),
                        (
                            "date_start_consumption",
                            ">=",
                            date,
                        ),
                        (
                            "date_end_consumption",
                            "<=",
                            date,
                        ),
                    ]
                )

                if item:
                    pricelist_info = PmsPricelistItemInfo(
                        roomTypeId=room_type.id,
                        date=str(
                            datetime.combine(date, datetime.min.time()).isoformat()
                        ),
                    )

                    pricelist_info.pricelistItemId = item.id
                    price = re.findall(r"[+-]?\d+\.\d+", item.price)
                    pricelist_info.price = float(price[0])

                    result.append(pricelist_info)

        return result

    @restapi.method(
        [
            (
                [
                    "/<int:pricelist_id>/pricelist-items",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.pricelist.item.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_pricelist_item(self, pricelist_id, pms_pricelist_item_info):
        day = datetime.strptime(
            pms_pricelist_item_info.date[:10], "%Y-%m-%d"
        ) + timedelta(days=1)
        product_id = (
            self.env["pms.room.type"]
            .browse(pms_pricelist_item_info.roomTypeId)
            .product_id
        )
        pricelist_item = self.env["product.pricelist.item"].create(
            {
                "applied_on": "0_product_variant",
                "product_id": product_id.id,
                "pms_property_ids": [pms_pricelist_item_info.pmsPropertyId],
                "date_start_consumption": day,
                "date_end_consumption": day,
                "compute_price": "fixed",
                "fixed_price": pms_pricelist_item_info.price,
                "pricelist_id": pricelist_id,
            }
        )
        return pricelist_item.id

    @restapi.method(
        [
            (
                [
                    "/<int:pricelist_id>/pricelist-items/<int:pricelist_item_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.pricelist.item.info", is_list=False),
        auth="jwt_api_pms",
    )
    def write_pricelist_item(
        self, pricelist_id, pricelist_item_id, pms_pricelist_item_info
    ):

        product_pricelist_item = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", pricelist_id),
                ("id", "=", pricelist_item_id),
            ]
        )
        if product_pricelist_item and pms_pricelist_item_info.price:
            product_pricelist_item.write(
                {
                    "fixed_price": pms_pricelist_item_info.price,
                }
            )
