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
        pms_property = self.env["pms.property"].browse(
            pricelist_item_search_param.pmsPropertyId
        )
        date_from = datetime.strptime(
            pricelist_item_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            pricelist_item_search_param.dateTo, "%Y-%m-%d"
        ).date()
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        record_pricelist = self.env["product.pricelist"].search(
            [("id", "=", pricelist_id)]
        )
        if not record_pricelist:
            raise MissingError
        rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", pricelist_item_search_param.pmsPropertyId)]
        )
        room_types = rooms.mapped("room_type_id")
        result = []
        PmsPricelistItemInfo = self.env.datamodels["pms.pricelist.item.info"]
        for date in target_dates:
            products = [(product, 1, False) for product in room_types.product_id]
            date_prices = record_pricelist.with_context(
                quantity=1,
                consumption_date=date,
                property=pms_property.id,
            )._compute_price_rule(products, datetime.today())
            for product_id, v in date_prices.items():
                room_type_id = (
                    self.env["product.product"].browse(product_id).room_type_id.id
                )
                if not v[1]:
                    continue
                pricelist_info = PmsPricelistItemInfo(
                    roomTypeId=room_type_id,
                    date=str(datetime.combine(date, datetime.min.time()).isoformat()),
                    pricelistItemId=v[1],
                    price=v[0],
                )
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
