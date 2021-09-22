# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsRoomTypeClassDelayedBatchExporter(Component):
    _name = "channel.wubook.pms.room.type.class.delayed.batch.exporter"
    _inherit = "channel.wubook.delayed.batch.exporter"

    _apply_on = "channel.wubook.pms.room.type.class"


class ChannelWubookPmsRoomTypeClassDirectBatchExporter(Component):
    _name = "channel.wubook.pms.room.type.class.direct.batch.exporter"
    _inherit = "channel.wubook.direct.batch.exporter"

    _apply_on = "channel.wubook.pms.room.type.class"


class ChannelWubookPmsRoomTypeClassExporter(Component):
    _name = "channel.wubook.pms.room.type.class.exporter"
    _inherit = "channel.wubook.exporter"

    _apply_on = "channel.wubook.pms.room.type.class"

    def _has_to_skip(self):
        return any(
            [
                self.binding.default_code
                in self.backend_record.backend_type_id.child_id.room_type_class_ids.get_nosync_shortnames(),
            ]
        )
