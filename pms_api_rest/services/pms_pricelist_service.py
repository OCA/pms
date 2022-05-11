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
        if pms_search_param.pms_property_ids:
            pricelists = set()
            for index, prop in enumerate(pms_search_param.pms_property_ids):
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
                    pms_property_ids=pricelist.pms_property_ids.mapped("id"),
                )
            )
        return result_pricelists

    @restapi.method(
        [
            (
                [
                    "/<int:pricelist_id>",
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
            [("pms_property_id", "=", pricelist_item_search_param.pms_property_id)]
        )
        date_from = datetime.strptime(
            pricelist_item_search_param.date_from, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            pricelist_item_search_param.date_to, "%Y-%m-%d"
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

                    if item:
                        pricelist_info.pricelistItemId = item.id
                        price = re.findall("[+-]?\d+\.\d+", item.price)
                        pricelist_info.price = float(price[0])

                    result.append(pricelist_info)

        return result
