# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ChannelWubookPmsAvailabilityPlanMapperImport(Component):
    _name = "channel.wubook.pms.availability.plan.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.availability.plan"

    direct = [
        ("name", "name"),
    ]

    children = [
        (
            "items",
            "channel_wubook_rule_ids",
            "channel.wubook.pms.availability.plan.rule",
        )
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def property_ids(self, record):
        binding = self.options.get("binding")
        has_pms_properties = binding and bool(binding.pms_property_ids)
        if self.options.for_create or has_pms_properties:
            return {
                "pms_property_ids": [(4, self.backend_record.pms_property_id.id, 0)]
            }


class ChannelWubookPmsAvailabilityPlanChildBinderMapperImport(Component):
    _name = "channel.wubook.pms.availability.plan.child.binder.mapper.import"
    _inherit = "channel.wubook.child.binder.mapper.import"
    _apply_on = "channel.wubook.pms.availability.plan.rule"

    def get_item_values(self, map_record, to_attr, options):
        values = super().get_item_values(map_record, to_attr, options)
        binding = options.get("binding")
        if binding:
            item_ids = binding.rule_ids.filtered(
                lambda x: all(
                    [
                        x.date == values["date"],
                        x.room_type_id.id == values["room_type_id"],
                        x.pms_property_id == self.backend_record.pms_property_id,
                    ]
                )
            )
            if item_ids:
                if len(item_ids) > 1:
                    raise ValidationError(
                        _(
                            "Found two Plan Rules with same data %s. "
                            "Please remove one of them"
                        )
                        % values
                    )
                item_binding = self.binder_for().wrap_record(item_ids)
                if item_binding:
                    values["id"] = item_binding.id
                else:
                    values["odoo_id"] = item_ids.id

        return values

    def format_items(self, items_values):
        ops = []
        items_values = sorted(
            items_values, key=lambda x: (x["room_type_id"], x["date"]), reverse=True
        )
        # TODO: the next code is always the same, put it on a common parent
        for values in items_values:
            _id = values.pop("id", None)
            if _id:
                ops.append((1, _id, values))
            else:
                ops.append((0, 0, values))

        return ops
