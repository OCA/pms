# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector_pms.components.adapter import ChannelAdapterError

RESTRICTION_FIELDS_IMPORT = [
    "closed_arrival",
    "closed",
    "min_stay",
    "closed_departure",
    "max_stay",
    "min_stay_arrival",
]
# Workaround to Wubook bug
# Wubook API does not return this on 'rplan_get_rplan_values'
# but you can write this value with 'rplan_update_rplan_values'
# All fields should be all together under single field RESTRICTION_FIELDS
RESTRICTION_FIELDS_EXPORT = RESTRICTION_FIELDS_IMPORT + [
    "max_stay_arrival",
]

AVAILABILITY_FIELDS = ["no_ota", "avail"]

ID_WUBOOK_PLAN = -1


class ChannelWubookPmsAvailabilityPlanAdapter(Component):
    _name = "channel.wubook.pms.availability.plan"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.pms.availability.plan"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_add_rplan

        # plan values
        if "compact" not in values:
            values["compact"] = 0
        if values["compact"] != 0:
            raise ChannelAdapterError(_("Compact type plan is currently not supported"))

        params = self._prepare_parameters(
            {k: values[k] for k in values if k in {"name", "compact"}},
            ["name", "compact"],
        )
        _id = self._exec("rplan_add_rplan", *params)

        # rule item values
        items = values.get("items")
        if items:
            try:
                self._write_items(_id, items)
            except ChannelAdapterError:
                self.delete(_id)
                raise

        return _id

    def read(self, _id):
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_rplans
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_get_rplan_values
        values = self.search_read([("id", "=", _id)])
        if not values:
            return False
        if len(values) != 1:
            raise ChannelAdapterError(_("Received more than one plan %s") % (values,))
        return values[0]

    def search_read(self, domain):
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_rplans
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_get_rplan_values
        # https://tdocs.wubook.net/wired/avail.html#fetch_rooms_values
        all_plans = self._exec("rplan_rplans")
        all_plans.append(
            {
                "id": ID_WUBOOK_PLAN,
                "name": "Wubook Restrictions",
            }
        )

        real_domain, common_domain = self._extract_domain_clauses(
            domain, ["date", "id_room"]
        )
        room_domain, real_domain = self._extract_domain_clauses(
            real_domain, ["id_room"]
        )
        base_plans = self._filter(all_plans, common_domain)
        if real_domain:
            for base_chunk_plan in self.chunks(base_plans, 6):
                kw_base_params = self._domain_to_normalized_dict(real_domain, "date")

                plans_values = {}
                # get wubook plan values
                # fetch_rooms_values(token, lcode, dfrom, dto[, rooms])
                plan_zero = [x for x in base_chunk_plan if x["id"] == ID_WUBOOK_PLAN]
                if plan_zero:
                    if len(plan_zero) > 1:
                        raise ValidationError(
                            _("Unexpected two elements with same id %s") % plan_zero
                        )
                    params = self._prepare_parameters(
                        kw_base_params, ["date_from", "date_to"], ["rooms"]
                    )
                    plan_zero_values = self._exec("fetch_rooms_values", *params)
                    for id_room, rooms in plan_zero_values.items():
                        for room in rooms:
                            room["id_room"] = int(id_room)
                    plans_values[str(ID_WUBOOK_PLAN)] = plan_zero_values

                    # get regular plan values
                # rplan_get_rplan_values(token, lcode, dfrom, dto[, rpids])
                kw_params = {
                    "rpids": [
                        x["id"] for x in base_chunk_plan if x["id"] != ID_WUBOOK_PLAN
                    ],
                    **kw_base_params,
                }
                params = self._prepare_parameters(
                    kw_params, ["date_from", "date_to"], ["rpids"]
                )
                plans_values.update(self._exec("rplan_get_rplan_values", *params))

                # get availability data
                rooms = set()
                for plan_rooms in plans_values.values():
                    rooms |= {int(x) for x in plan_rooms.keys()}
                kw_params = {"rooms": list(rooms), **kw_base_params}
                params = self._prepare_parameters(
                    kw_params, ["date_from", "date_to"], ["rooms"]
                )
                avail_values = self._exec("fetch_rooms_values", *params)

                date_from = datetime.datetime.strptime(
                    kw_base_params["date_from"], self._date_format
                ).date()
                for plan in base_chunk_plan:
                    plan["items"] = []
                    for id_room, room in plans_values[str(plan["id"])].items():
                        for day in range(len(room)):
                            plan["items"].append(
                                {
                                    **{
                                        x: room[day][x]
                                        for x in RESTRICTION_FIELDS_IMPORT + ["id_room"]
                                    },
                                    **{
                                        x: avail_values[id_room][day][x]
                                        for x in AVAILABILITY_FIELDS
                                    },
                                    "date": date_from + datetime.timedelta(days=day),
                                }
                            )
                    plan["items"] = self._filter(plan["items"], room_domain)

        self._format_data(base_plans)
        return base_plans

    def search(self, domain):
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_rplans
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_get_rplan_values
        values = self.search_read(domain)
        ids = [x[self._id] for x in values]
        return ids

    # pylint: disable=W8106
    def write(self, _id, values):
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_rename_rplan
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_get_rplan_values

        # plan values
        if "name" in values:
            params = self._prepare_parameters(
                {"id": _id, **{k: values[k] for k in values if k in {"name"}}},
                ["id", "name"],
            )
            self._exec("rplan_rename_rplan", *params)

        # rule item values
        items = values.get("items")
        if items:
            self._write_items(_id, items)

    def delete(self, _id):
        # https://tdocs.wubook.net/wired/rstrs.html#rplan_del_rplan
        params = self._prepare_parameters(
            {"id": _id},
            ["id"],
        )
        self._exec("rplan_del_rplan", *params)

    # aux
    def _write_items(self, _id, items):
        dates = {x["date"] for x in items}
        dfrom, dto = min(dates), max(dates)
        items_by_room = {}
        for room in items:
            if not isinstance(room["date"], datetime.date):
                raise ValidationError(
                    _("Date fields must be of type date, not %s") % type(room["date"])
                )
            items_by_room.setdefault(room["id_room"], {})
            if room["date"] in items_by_room[room["id_room"]]:
                raise ValidationError(_("The rooms exists twice with the same date"))
            items_by_room[room["id_room"]][room["date"]] = room

        all_rules_by_room, rules_by_room, avail_by_room = {}, {}, {}
        rules_by_room = {}
        for id_room, room_by_date in items_by_room.items():
            for i in range((dto - dfrom).days + 1):
                date = dfrom + datetime.timedelta(days=i)
                room = room_by_date.get(date, {})
                all_rules_by_room.setdefault(id_room, []).append(
                    {
                        x: room[x]
                        for x in room
                        if x in RESTRICTION_FIELDS_EXPORT + AVAILABILITY_FIELDS
                    }
                )
                rules_by_room.setdefault(str(id_room), []).append(
                    {x: room[x] for x in room if x in RESTRICTION_FIELDS_EXPORT}
                )
                avail_by_room.setdefault(id_room, []).append(
                    {x: room[x] for x in room if x in AVAILABILITY_FIELDS}
                )

        # if rules_by_room:
        if _id == ID_WUBOOK_PLAN:
            # update_avail(token, lcode, dfrom, rooms)
            params = self._prepare_parameters(
                {
                    "dfrom": dfrom.strftime(self._date_format),
                    "rooms": [
                        {
                            "id": _id,
                            "days": list(days),
                        }
                        for _id, days in all_rules_by_room.items()
                    ],
                },
                ["dfrom", "rooms"],
            )
            self._exec("update_avail", *params)
        else:
            # rplan_update_rplan_values(token, lcode, pid, dfrom, values)
            params = self._prepare_parameters(
                {
                    "pid": _id,
                    "dfrom": dfrom.strftime(self._date_format),
                    "values": rules_by_room,
                },
                ["pid", "dfrom", "values"],
            )
            self._exec("rplan_update_rplan_values", *params)

            # update_avail(token, lcode, dfrom, rooms)
            params = self._prepare_parameters(
                {
                    "dfrom": dfrom.strftime(self._date_format),
                    "rooms": [
                        {
                            "id": _id,
                            "days": list(days),
                        }
                        for _id, days in avail_by_room.items()
                    ],
                },
                ["dfrom", "rooms"],
            )
            self._exec("update_avail", *params)

    def _format_data(self, values):
        conv_mapper = {
            "/items/closed_departure": lambda x: int(x),
        }
        self._convert_format(values, conv_mapper)
