# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsRoomTypeDelayedBatchExporter(Component):
    _name = "channel.wubook.pms.room.type.delayed.batch.exporter"
    _inherit = "channel.wubook.delayed.batch.exporter"

    _apply_on = "channel.wubook.pms.room.type"


class ChannelWubookPmsRoomTypeDirectBatchExporter(Component):
    _name = "channel.wubook.pms.room.type.direct.batch.exporter"
    _inherit = "channel.wubook.direct.batch.exporter"

    _apply_on = "channel.wubook.pms.room.type"


class ChannelWubookPmsRoomTypeExporter(Component):
    _name = "channel.wubook.pms.room.type.exporter"
    _inherit = "channel.wubook.exporter"

    _apply_on = "channel.wubook.pms.room.type"

    def _export_dependencies(self):
        self._export_dependency(
            self.binding.class_id, "channel.wubook.pms.room.type.class"
        )
        for board_service in self.binding.board_service_room_type_ids.mapped(
            "pms_board_service_id"
        ):
            self._export_dependency(board_service, "channel.wubook.pms.board.service")

    def _has_to_skip(self):
        return any(
            [
                self.binding.class_id.default_code
                in self.backend_record.backend_type_id.child_id.room_type_class_ids.get_nosync_shortnames(),
            ]
        )

    def _force_binding_creation(self, relation):
        pass
