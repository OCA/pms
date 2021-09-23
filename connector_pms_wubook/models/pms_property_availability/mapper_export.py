# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsPropertyAvailabilityMapperExport(Component):
    _name = "channel.wubook.pms.property.availability.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.pms.property.availability"

    children = [
        (
            "channel_wubook_availability_ids",
            "availabilities",
            "channel.wubook.pms.availability",
        )
    ]


class ChannelWubookPmsPropertyAvailabilityChildBinderMapperExport(Component):
    _name = "channel.wubook.pms.property.availability.child.binder.mapper.export"
    _inherit = "channel.wubook.child.binder.mapper.export"
    _apply_on = "channel.wubook.pms.availability"

    def skip_item(self, map_record):
        # TODO: filter this on get_all_items, creating a hook on the mapper
        #   to allow filtering them overriding the hook
        return any(
            [
                map_record.source.room_type_id.class_id.default_code
                in self.backend_record.backend_type_id.child_id.room_type_class_ids.get_nosync_shortnames(),
                map_record.source.synced_export,
                not map_record.source.odoo_id.wubook_date_valid(),
            ]
        )

    def get_all_items(self, mapper, items, parent, to_attr, options):
        # TODO: this is always the same on every child binder mapper
        #   except 'rule_ids' try to move it to the parent
        bindings = items.filtered(lambda x: x.backend_id == self.backend_record)
        new_bindings = parent.source["availability_ids"].filtered(
            lambda x: self.backend_record not in x.channel_wubook_bind_ids.backend_id
        )
        items = (
            items.browse(
                [self.binder_for().wrap_record(x, force=True).id for x in new_bindings]
            )
            | bindings
        )
        mapper = super().get_all_items(mapper, items, parent, to_attr, options)
        return mapper
