from datetime import datetime, timedelta

from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAvailabilityPlanService(Component):
    _inherit = "base.rest.service"
    _name = "pms.availability.plan.service"
    _usage = "availability-plans"
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
        output_param=Datamodel("pms.availability.plan.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_availability_plans(self, pms_search_param, **args):

        availability_plans_all_properties = self.env["pms.availability.plan"].search(
            [("pms_property_ids", "=", False)]
        )
        availabilities = set()
        if pms_search_param.pms_property_ids:
            for index, prop in enumerate(pms_search_param.pms_property_ids):
                availabilities_with_query_property = self.env[
                    "pms.availability.plan"
                ].search([("pms_property_ids", "=", prop)])
                if index == 0:
                    availabilities = set(availabilities_with_query_property.ids)
                else:
                    availabilities = availabilities.intersection(
                        set(availabilities_with_query_property.ids)
                    )
            availabilities_total = list(
                set(list(availabilities) + availability_plans_all_properties.ids)
            )
        else:
            availabilities_total = list(availability_plans_all_properties.ids)
        domain = [
            ("id", "in", availabilities_total),
        ]

        PmsAvialabilityPlanInfo = self.env.datamodels["pms.availability.plan.info"]
        result_availabilities = []
        for availability in self.env["pms.availability.plan"].search(domain):
            result_availabilities.append(
                PmsAvialabilityPlanInfo(
                    id=availability.id,
                    name=availability.name,
                    pms_property_ids=availability.pms_property_ids.mapped("id"),
                )
            )
        return result_availabilities

    @restapi.method(
        [
            (
                [
                    "/<int:availability_plan>",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.availability.plan.rule.search.param", is_list=False),
        output_param=Datamodel("pms.availability.plan.rule.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_availability_plan_rules(
        self, availability_plan_id, availability_plan_rule_search_param
    ):
        result = []
        record_availability_plan_id = self.env["pms.availability.plan"].browse(
            availability_plan_id
        )
        if not record_availability_plan_id:
            raise MissingError
        PmsAvailabilityPlanInfo = self.env.datamodels["pms.availability.plan.rule.info"]
        rooms = self.env["pms.room"].search(
            [
                (
                    "pms_property_id",
                    "=",
                    availability_plan_rule_search_param.pms_property_id,
                )
            ]
        )
        date_from = datetime.strptime(
            availability_plan_rule_search_param.date_from, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            availability_plan_rule_search_param.date_to, "%Y-%m-%d"
        ).date()

        for date in (
            date_from + timedelta(d) for d in range((date_to - date_from).days + 1)
        ):
            for room_type in self.env["pms.room.type"].search(
                [("id", "in", rooms.mapped("room_type_id").ids)]
            ):
                rule = self.env["pms.availability.plan.rule"].search(
                    [
                        ("date", "=", date),
                        (
                            "availability_plan_id",
                            "=",
                            record_availability_plan_id.id,
                        ),
                        ("room_type_id", "=", room_type.id),
                    ]
                )
                if rule:
                    availability_plan_rule_info = PmsAvailabilityPlanInfo(
                        roomTypeId=room_type.id,
                        date=str(
                            datetime.combine(date, datetime.min.time()).isoformat()
                        ),
                    )

                    if rule:

                        availability_plan_rule_info.availabilityRuleId = rule.id
                        availability_plan_rule_info.minStay = rule.min_stay
                        availability_plan_rule_info.minStayArrival = (
                            rule.min_stay_arrival
                        )
                        availability_plan_rule_info.maxStay = rule.max_stay
                        availability_plan_rule_info.maxStayArrival = (
                            rule.max_stay_arrival
                        )
                        availability_plan_rule_info.closed = rule.closed
                        availability_plan_rule_info.closedDeparture = (
                            rule.closed_departure
                        )
                        availability_plan_rule_info.closedArrival = rule.closed_arrival
                        availability_plan_rule_info.quota = rule.quota

                    result.append(availability_plan_rule_info)

        return result
