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
        if pms_search_param.pmsPropertyIds:
            for index, prop in enumerate(pms_search_param.pmsPropertyIds):
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
                    pmsPropertyIds=availability.pms_property_ids.mapped("id"),
                )
            )
        return result_availabilities

    @restapi.method(
        [
            (
                [
                    "/<int:availability_plan>/availability-plan-rules",
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
        date_from = datetime.strptime(
            availability_plan_rule_search_param.dateFrom, "%Y-%m-%d"
        ).date()
        date_to = datetime.strptime(
            availability_plan_rule_search_param.dateTo, "%Y-%m-%d"
        ).date()
        count_nights = (date_to - date_from).days + 1
        target_dates = [date_from + timedelta(days=x) for x in range(count_nights)]
        pms_property_id = availability_plan_rule_search_param.pmsPropertyId
        record_availability_plan_id = self.env["pms.availability.plan"].browse(
            availability_plan_id
        )
        if not record_availability_plan_id:
            raise MissingError

        rooms = self.env["pms.room"].search(
            [
                (
                    "pms_property_id",
                    "=",
                    availability_plan_rule_search_param.pmsPropertyId,
                )
            ]
        )
        room_type_ids = rooms.mapped("room_type_id").ids
        selected_fields = [
            "id",
            "date",
            "room_type_id",
            "min_stay",
            "min_stay_arrival",
            "max_stay",
            "max_stay_arrival",
            "closed",
            "closed_departure",
            "closed_arrival",
            "quota",
            "max_avail",
        ]
        sql_select = "SELECT %s" % ", ".join(selected_fields)
        self.env.cr.execute(
            f"""
            {sql_select}
            FROM    pms_availability_plan_rule  rule
            WHERE   (pms_property_id = %s)
                AND (date in %s)
                AND (availability_plan_id = %s)
                AND (room_type_id in %s)
            """,
            (
                pms_property_id,
                tuple(target_dates),
                record_availability_plan_id.id,
                tuple(room_type_ids),
            ),
        )
        result_sql = self.env.cr.fetchall()
        rules = []
        for res in result_sql:
            rules.append(
                {field: res[selected_fields.index(field)] for field in selected_fields}
            )

        result = []
        PmsAvailabilityPlanRuleInfo = self.env.datamodels[
            "pms.availability.plan.rule.info"
        ]

        for date in target_dates:
            for room_type_id in room_type_ids:
                rule = next(
                    (
                        rule
                        for rule in rules
                        if rule["room_type_id"] == room_type_id and rule["date"] == date
                    ),
                    False,
                )

                if rule:
                    availability_plan_rule_info = PmsAvailabilityPlanRuleInfo(
                        roomTypeId=rule["room_type_id"],
                        date=datetime.combine(date, datetime.min.time()).isoformat(),
                        availabilityRuleId=rule["id"],
                        minStay=rule["min_stay"],
                        minStayArrival=rule["min_stay_arrival"],
                        maxStay=rule["max_stay"],
                        maxStayArrival=rule["max_stay_arrival"],
                        closed=rule["closed"],
                        closedDeparture=rule["closed_departure"],
                        closedArrival=rule["closed_arrival"],
                        quota=rule["quota"],
                        maxAvailability=rule["max_avail"],
                        availabilityPlanId=availability_plan_id,
                    )
                    result.append(availability_plan_rule_info)

        return result

    @restapi.method(
        [
            (
                [
                    "/<int:availability_plan_id>/availability-plan-rules",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.availability.plan.rules.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_availability_plan_rule(
        self, availability_plan_id, pms_avail_plan_rules_info
    ):
        for avail_plan_rule in pms_avail_plan_rules_info.availabilityPlanRules:
            vals = dict()
            date = datetime.strptime(avail_plan_rule.date, "%Y-%m-%d").date()
            if avail_plan_rule.minStay is not None:
                vals.update({"min_stay": avail_plan_rule.minStay})
            if avail_plan_rule.minStayArrival is not None:
                vals.update({"min_stay_arrival": avail_plan_rule.minStayArrival})
            if avail_plan_rule.maxStay is not None:
                vals.update({"max_stay": avail_plan_rule.maxStay})
            if avail_plan_rule.maxStayArrival is not None:
                vals.update({"max_stay_arrival": avail_plan_rule.maxStayArrival})
            if avail_plan_rule.closed is not None:
                vals.update({"closed": avail_plan_rule.closed})
            if avail_plan_rule.closedDeparture is not None:
                vals.update({"closed_departure": avail_plan_rule.closedDeparture})
            if avail_plan_rule.closedArrival is not None:
                vals.update({"closed_arrival": avail_plan_rule.closedArrival})
            if avail_plan_rule.quota is not None:
                vals.update({"quota": avail_plan_rule.quota})
            if avail_plan_rule.maxAvailability is not None:
                vals.update({"max_avail": avail_plan_rule.maxAvailability})
            avail_rule = self.env["pms.availability.plan.rule"].search(
                [
                    ("availability_plan_id", "=", avail_plan_rule.availabilityPlanId),
                    ("pms_property_id", "=", avail_plan_rule.pmsPropertyId),
                    ("room_type_id", "=", avail_plan_rule.roomTypeId),
                    ("date", "=", date),
                ]
            )
            if avail_rule:
                avail_rule.write(vals)
            else:
                vals.update(
                    {
                        "room_type_id": avail_plan_rule.roomTypeId,
                        "date": date,
                        "pms_property_id": avail_plan_rule.pmsPropertyId,
                        "availability_plan_id": avail_plan_rule.availabilityPlanId,
                    }
                )
                self.env["pms.availability.plan.rule"].create(vals)
