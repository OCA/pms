# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsAvailabilityDelayedBatchExporter(Component):
    _name = "channel.wubook.pms.availability.delayed.batch.exporter"
    _inherit = "channel.wubook.delayed.batch.exporter"

    _apply_on = "channel.wubook.pms.availability"


class ChannelWubookPmsAvailabilityDirectBatchExporter(Component):
    _name = "channel.wubook.pms.availability.direct.batch.exporter"
    _inherit = "channel.wubook.direct.batch.exporter"

    _apply_on = "channel.wubook.pms.availability"


class ChannelWubookPmsAvailabilityExporter(Component):
    _name = "channel.wubook.pms.availability.exporter"
    _inherit = "channel.wubook.exporter"

    _apply_on = "channel.wubook.pms.availability"

    def _export_dependencies(self):
        self._export_dependency(
            self.binding.room_type_id, "channel.wubook.pms.room.type"
        )
