# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsAvailabilityPlanMapperExport(Component):
    _name = "channel.wubook.pms.availability.plan.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.pms.availability.plan"

    direct = [
        ("name", "name"),
    ]

    children = [
        (
            "channel_wubook_rule_ids",
            "items",
            "channel.wubook.pms.availability.plan.rule",
        )
    ]


class ChannelWubookPmsAvailabilityPlanChildMapperExport(Component):
    _name = "channel.wubook.pms.availability.plan.child.mapper.export"
    _inherit = "channel.wubook.child.mapper.export"
    _apply_on = "channel.wubook.pms.availability.plan.rule"

    def skip_item(self, map_record):
        return map_record.source.pms_property_id != self.backend_record.pms_property_id
        # or \
        # (map_record.parent.source.sync_date_export and
        #  map_record.parent.source.sync_date_export >= map_record.source.write_date)
