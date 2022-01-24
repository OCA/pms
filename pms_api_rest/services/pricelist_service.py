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
        input_param=Datamodel("pms.pricelist.info", is_list=False),
        output_param=Datamodel("pms.pricelist.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_pricelists(self, pricelist_info_search_param, **args):
        domain = []
        if pricelist_info_search_param.pms_property_id:
            domain.append(
                (
                    "pms_property_ids",
                    "in",
                    [pricelist_info_search_param.pms_property_id],
                )
            )
        PmsPricelistInfo = self.env.datamodels["pms.pricelist.info"]
        result_pricelists = []
        for pricelist in self.env["product.pricelist"].sudo().search(domain):
            result_pricelists.append(
                PmsPricelistInfo(
                    id=pricelist.id,
                    name=pricelist.name,
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
        record_pricelist_id = (
            self.env["product.pricelist"].sudo().search([("id", "=", pricelist_id)])
        )
        if not record_pricelist_id:
            raise MissingError
        PmsPricelistItemInfo = self.env.datamodels["pms.pricelist.item.info"]
        rooms = (
            self.env["pms.room"]
            .sudo()
            .search(
                [("pms_property_id", "=", pricelist_item_search_param.pms_property_id)]
            )
        )
        for room_type in (
            self.env["pms.room.type"]
            .sudo()
            .search([("id", "in", rooms.mapped("room_type_id").ids)])
        ):
            for item in (
                self.env["product.pricelist.item"]
                .sudo()
                .search(
                    [
                        ("pricelist_id", "=", pricelist_id),
                        ("applied_on", "=", "0_product_variant"),
                        ("product_id", "=", room_type.product_id.id),
                        (
                            "date_start_consumption",
                            ">=",
                            pricelist_item_search_param.date_from,
                        ),
                        (
                            "date_end_consumption",
                            "<=",
                            pricelist_item_search_param.date_to,
                        ),
                    ]
                )
            ):
                rule = (
                    self.env["pms.availability.plan.rule"]
                    .sudo()
                    .search(
                        [
                            (
                                "availability_plan_id",
                                "=",
                                record_pricelist_id.availability_plan_id.id,
                            ),
                            ("date", "=", item.date_start_consumption),
                            ("date", "=", item.date_end_consumption),
                            ("room_type_id", "=", room_type.id),
                            (
                                "pms_property_id",
                                "=",
                                pricelist_item_search_param.pms_property_id,
                            ),
                        ]
                    )
                )
                rule.ensure_one()
                result.append(
                    PmsPricelistItemInfo(
                        pricelist_item_id=item.id,
                        availability_rule_id=rule.id,
                        room_type_id=room_type.id,
                        fixed_price=item.fixed_price,
                        min_stay=rule.min_stay,
                        min_stay_arrival=rule.min_stay_arrival,
                        max_stay=rule.max_stay,
                        max_stay_arrival=rule.max_stay_arrival,
                        closed=rule.closed,
                        closed_departure=rule.closed_departure,
                        closed_arrival=rule.closed_arrival,
                        quota=rule.quota,
                        max_avail=rule.max_avail,
                        date=str(item.date_start_consumption),
                    )
                )
        return result