from datetime import datetime, timedelta

from odoo import _
from odoo.exceptions import MissingError, ValidationError

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
        input_param=Datamodel("pms.pricelist.search", is_list=False),
        output_param=Datamodel("pms.pricelist.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_pricelists(self, pms_search_param, **args):
        pricelists = self.env["product.pricelist"].search([])
        if pms_search_param.pmsPropertyIds and pms_search_param.pmsPropertyId:
            raise ValidationError(
                _(
                    """
                Simultaneous search by list of properties and by specific property:
                make sure to use only one of the two search parameters
                """
                )
            )
        if pms_search_param.pmsPropertyIds:
            pricelists = pricelists.filtered(
                lambda p: not p.pms_property_ids
                or all(
                    item in p.pms_property_ids.ids
                    for item in pms_search_param.pmsPropertyIds
                )
            )
        if pms_search_param.pmsPropertyId:
            pricelists = pricelists.filtered(
                lambda p: not p.pms_property_ids
                or pms_search_param.pmsPropertyId in p.pms_property_ids.ids
            )
        if pms_search_param.saleChannelId:
            pricelists = pricelists.filtered(
                lambda p: not p.pms_sale_channel_ids
                or pms_search_param.saleChannelId in p.pms_sale_channel_ids.ids
            )
        PmsPricelistInfo = self.env.datamodels["pms.pricelist.info"]
        result_pricelists = []
        for pricelist in pricelists:
            result_pricelists.append(
                PmsPricelistInfo(
                    id=pricelist.id,
                    name=pricelist.name,
                    cancelationRuleId=pricelist.cancelation_rule_id.id
                    if pricelist.cancelation_rule_id
                    else None,
                    defaultAvailabilityPlanId=pricelist.availability_plan_id.id
                    if pricelist.availability_plan_id
                    else None,
                    pmsPropertyIds=pricelist.pms_property_ids.ids,
                    saleChannelIds=pricelist.pms_sale_channel_ids.ids,
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

                    pricelist_info.pricelistItemId = item[0].id
                    pricelist_info.price = item[0].fixed_price

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
        input_param=Datamodel("pms.pricelist.items.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_pricelist_item(self, pricelist_id, pms_pricelist_item_info):
        for pms_pricelist_item in pms_pricelist_item_info.pricelistItems:
            date = datetime.strptime(pms_pricelist_item.date, "%Y-%m-%d").date()
            product_id = (
                self.env["pms.room.type"]
                .browse(pms_pricelist_item.roomTypeId)
                .product_id
            )
            product_pricelist_item = self.env["product.pricelist.item"].search(
                [
                    ("pricelist_id", "=", pms_pricelist_item.pricelistId),
                    ("product_id", "=", product_id.id),
                    ("pms_property_ids", "in", pms_pricelist_item.pmsPropertyId),
                    ("date_start_consumption", "=", date),
                    ("date_end_consumption", "=", date),
                ]
            )
            if product_pricelist_item:
                product_pricelist_item.write(
                    {
                        "fixed_price": pms_pricelist_item.price,
                    }
                )
            else:
                self.env["product.pricelist.item"].create(
                    {
                        "applied_on": "0_product_variant",
                        "product_id": product_id.id,
                        "pms_property_ids": [pms_pricelist_item.pmsPropertyId],
                        "date_start_consumption": date,
                        "date_end_consumption": date,
                        "compute_price": "fixed",
                        "fixed_price": pms_pricelist_item.price,
                        "pricelist_id": pms_pricelist_item.pricelistId,
                    }
                )
