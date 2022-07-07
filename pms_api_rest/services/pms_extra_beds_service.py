from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsExtraBedsService(Component):
    _inherit = "base.rest.service"
    _name = "pms.extra.beds.service"
    _usage = "extra-beds"
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
        input_param=Datamodel("pms.extra.beds.search.param"),
        output_param=Datamodel("pms.extra.bed.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_extra_beds(self, extra_beds_search_param):
        domain = [("is_extra_bed", "=", True)]
        if extra_beds_search_param.name:
            domain.append(("name", "like", extra_beds_search_param.name))
        if extra_beds_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    ("pms_property_ids", "in", extra_beds_search_param.pmsPropertyId),
                    ("pms_property_ids", "=", False),
                ]
            )

        result_extra_beds = []
        PmsExtraBed = self.env.datamodels["pms.extra.bed.info"]

        for bed in self.env["product.product"].search(
            domain,
        ):
            avail = -1
            if extra_beds_search_param.dateFrom and extra_beds_search_param.dateTo:
                qty_for_day = self.env["pms.service.line"].read_group(
                    [
                        ("product_id", "=", bed.id),
                        ("date", ">=", extra_beds_search_param.dateFrom),
                        ("date", "<=", extra_beds_search_param.dateTo),
                        ("cancel_discount", "=", 0),
                    ],
                    ["day_qty:sum"],
                    ["date:day"],
                )
                max_daily_used = (
                    max(date["day_qty"] for date in qty_for_day) if qty_for_day else 0
                )

                avail = bed.daily_limit - max_daily_used
                # Avoid send negative values in avail
                avail = avail if avail >= 0 else 0

            result_extra_beds.append(
                PmsExtraBed(
                    id=bed.id,
                    name=bed.name,
                    dailyLimitConfig=bed.daily_limit,
                    dailyLimitAvail=avail,
                )
            )

        return result_extra_beds
