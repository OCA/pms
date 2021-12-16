# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsPropertyAvailabilityDelayedBatchExporter(Component):
    _name = "channel.wubook.pms.property.availability.delayed.batch.exporter"
    _inherit = "channel.wubook.delayed.batch.exporter"

    _apply_on = "channel.wubook.pms.property.availability"


class ChannelWubookPmsPropertyAvailabilityDirectBatchExporter(Component):
    _name = "channel.wubook.pms.property.availability.direct.batch.exporter"
    _inherit = "channel.wubook.direct.batch.exporter"

    _apply_on = "channel.wubook.pms.property.availability"


class ChannelWubookPmsPropertyAvailabilityExporter(Component):
    _name = "channel.wubook.pms.property.availability.exporter"
    _inherit = "channel.wubook.exporter"

    _apply_on = "channel.wubook.pms.property.availability"

    # def _export_dependencies(self):
    #     for room_type in self.binding.availability_ids.mapped("room_type_id"):
    #         self._export_dependency(room_type, "channel.wubook.pms.room.type")
