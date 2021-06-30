# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component

# TODO: use these connector exception on every adapter
from odoo.addons.connector.exception import ManyIDSInBackend


class ChannelWubookProductPricelistAdapter(Component):
    _name = "channel.wubook.product.pricelist.adapter"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.product.pricelist"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        # TODO: share common code from write method and availability plan
        # https://tdocs.wubook.net/wired/prices.html#add_vplan
        # https://tdocs.wubook.net/wired/prices.html#add_pricing_plan
        # https://tdocs.wubook.net/wired/prices.html#update_plan_prices
        if "type" not in values:
            raise ValidationError(_("Type of plan is required"))

        # pricelist values
        if values.get("daily") == 0:
            raise ValidationError(_("Intensive plans not supported"))

        params = self._prepare_parameters(
            {k: values[k] for k in values if k in {"name", "daily"}},
            ["name"],
            ["daily"],
        )
        _id = self._exec("add_pricing_plan", *params)

        # pricelist item values
        items = values.get("items")
        if items:
            try:
                ttype = values["type"]
                if ttype == "virtual":
                    if len(items) != 1:
                        raise ValidationError(
                            _("Only one item of type 'virtual' allowed")
                        )
                    params = self._prepare_parameters(
                        {
                            "name": "v%s" % values["name"],
                            "vpid": _id,
                            **{k: items[0][k] for k in {"variation_type", "variation"}},
                        },
                        ["name", "vpid", "variation_type", "variation"],
                    )
                    self._exec("add_vplan", *params)
                elif ttype == "standard":
                    calls = self._smart_item_group(items)
                    for key, prices in calls.items():
                        dfrom = key[0]
                        params = self._prepare_parameters(
                            {
                                "id": _id,
                                "dfrom": dfrom.strftime(self._date_format),
                                "prices": prices,
                            },
                            ["id", "dfrom", "prices"],
                        )
                        self._exec("update_plan_prices", *params)
                else:
                    raise ValidationError(
                        _("Type %s not valid, only 'standard' and 'virtual' supported")
                        % ttype
                    )
            except ChannelAdapterError:
                self.delete(_id)
                raise

        return _id

    def read(self, _id):
        # https://tdocs.wubook.net/wired/prices.html#get_pricing_plans
        values = self.search_read([("id", "=", _id)])
        if not values:
            return False
        if len(values) > 1:
            raise ManyIDSInBackend(_("Received more than one room %s") % (values,))
        return values[0]

    def search_read(self, domain):
        # self._check_supported_domain_format(domain)
        # https://tdocs.wubook.net/wired/prices.html#get_pricing_plans
        all_plans = self._exec("get_pricing_plans")

        plans_by_id = {p["id"]: p for p in all_plans}

        # check pricelist external ID
        pl_external_id = self.backend_record.pricelist_external_id
        if pl_external_id not in plans_by_id:
            raise ValidationError(
                _(
                    "The External Parity Pricelist ID '%s' defined on the Backend "
                    "configuration does not exist on Backend.\nIt should be one of these: %s"
                )
                % (pl_external_id, all_plans)
            )

        # normalize pricing plans
        # - Adding 'type' to allow filtering by it
        # - Fix Wubook bug defining always daily=0 on all virtual plans
        # - Replace vpid == 0 (Parity) with actual pricelist mapped to it
        for plan in all_plans:
            if "vpid" in plan:
                plan["type"] = "virtual"
                if plan["vpid"] != 0:
                    plan["daily"] = plans_by_id[plan["vpid"]]["daily"]
            else:
                plan["type"] = "standard"

        for plan in all_plans:
            if "vpid" in plan:
                if plan["vpid"] == 0:
                    plan["vpid"] = self.backend_record.pricelist_external_id
                    plan["daily"] = plans_by_id[plan["vpid"]]["daily"]

        real_pl_domain, common_pl_domain = self._extract_domain_clauses(
            domain, ["date", "rooms"]
        )
        base_plans = self._filter(all_plans, common_pl_domain)
        res = []
        for plan in base_plans:
            values = {x: plan[x] for x in ["id", "name", "daily", "type"]}
            if values.get("daily") == 0:
                continue
            if "vpid" in plan:
                values["items"] = [
                    {x: plan[x] for x in {"vpid", "variation", "variation_type"}}
                ]
            else:
                if real_pl_domain:
                    kw_params = self._domain_to_normalized_dict(real_pl_domain, "date")
                    kw_params["id"] = plan["id"]
                    params = self._prepare_parameters(
                        kw_params, ["id", "date_from", "date_to"], ["rooms"]
                    )
                    date_from = datetime.datetime.strptime(
                        kw_params["date_from"], self._date_format
                    ).date()
                    items_raw = self._exec("fetch_plan_prices", *params)
                    items = []
                    for rid, prices in items_raw.items():
                        for i, price in enumerate(prices):
                            items.append(
                                {
                                    "rid": int(rid),
                                    "date": date_from + datetime.timedelta(days=i),
                                    "price": price,
                                }
                            )
                    values["items"] = items
            res.append(values)
        return res

    def search(self, domain):
        # https://tdocs.wubook.net/wired/prices.html#get_pricing_plans
        values = self.search_read(domain)
        ids = [x[self._id] for x in values]
        return ids

    # pylint: disable=W8106
    def write(self, _id, values):
        # TODO: share common code from create method and availability plan
        # https://tdocs.wubook.net/wired/prices.html#update_plan_name
        # https://tdocs.wubook.net/wired/prices.html#mod_vplans
        # https://tdocs.wubook.net/wired/prices.html#update_plan_prices
        if "type" not in values:
            raise ValidationError(_("Type of plan is required"))
        # pricelist values
        if values.get("daily") == 0:
            raise ValidationError(_("Intensive plans not supported"))
        if "name" in values:
            params = self._prepare_parameters(
                {"id": _id, **{k: values[k] for k in values if k in {"name"}}},
                ["id", "name"],
            )
            self._exec("update_plan_name", *params)

        # pricelist item values
        items = values.get("items")
        if items:
            ttype = values["type"]
            if ttype == "virtual":
                if len(items) != 1:
                    raise ValidationError(_("Only one item of type 'virtual' allowed"))
                params = self._prepare_parameters(
                    {
                        "plans": [
                            {
                                "pid": _id,
                                **{
                                    k: items[0][k]
                                    for k in {"variation_type", "variation"}
                                },
                            }
                        ]
                    },
                    ["plans"],
                )
                self._exec("mod_vplans", *params)
            elif ttype == "standard":
                calls = self._smart_item_group(items)
                for key, prices in calls.items():
                    dfrom = key[0]
                    params = self._prepare_parameters(
                        {
                            "id": _id,
                            "dfrom": dfrom.strftime(self._date_format),
                            "prices": prices,
                        },
                        ["id", "dfrom", "prices"],
                    )
                    self._exec("update_plan_prices", *params)
            else:
                raise ValidationError(
                    _("Type %s not valid, only 'standard' and 'virtual' supported")
                    % ttype
                )

    def delete(self, _id, cascade=False):
        # TODO: optimize
        # https://tdocs.wubook.net/wired/prices.html#del_plan
        if cascade:
            res = self.search_read([])
            for pl in res:
                if pl.get("items", {}).get("vpid") == _id:
                    self.delete(pl["id"], cascade=False)
        self._exec("del_plan", _id)

    # aux
    def _smart_item_group(self, items):
        # TODO: optimize and improve the grouping method,
        #  make it smarter
        def split_consecutive(items):
            res, ant, gr = {}, None, 0
            for item in items:
                cur = item["date"]
                if ant is not None:
                    if cur == ant or cur < ant:
                        raise Exception("Input not sorted!")
                    if cur != ant + datetime.timedelta(days=1):
                        gr += 1
                res.setdefault(gr, []).append(item)
                ant = cur
            return list(res.values())

        items_by_room = {}
        for item in sorted(items, key=lambda x: x["date"]):
            items_by_room.setdefault(item["rid"], []).append(item)

        items_by_dates = {}
        for rid, items in items_by_room.items():
            chunks = split_consecutive(items)
            for ch in chunks:
                key = tuple([x["date"] for x in ch])
                items_by_dates.setdefault(key, []).append(ch)

        calls = {}
        for key, chunks in items_by_dates.items():
            for ck in chunks:
                for e in ck:
                    calls.setdefault(key, {}).setdefault(str(e["rid"]), []).append(
                        e["price"]
                    )
        return calls
