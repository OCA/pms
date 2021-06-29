# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsAvailabilityDelayedBatchImporter(Component):
    _name = "channel.wubook.pms.availability.delayed.batch.importer"
    _inherit = "channel.wubook.delayed.batch.importer"

    _apply_on = "channel.wubook.pms.availability"


class ChannelWubookPmsAvailabilityDirectBatchImporter(Component):
    _name = "channel.wubook.pms.availability.direct.batch.importer"
    _inherit = "channel.wubook.direct.batch.importer"

    _apply_on = "channel.wubook.pms.availability"


class ChannelWubookPmsAvailabilityImporter(Component):
    _name = "channel.wubook.pms.availability.importer"
    _inherit = "channel.wubook.importer"

    _apply_on = "channel.wubook.pms.availability"

    def _import_dependencies(self, external_data, external_fields):
        self._import_dependency(
            external_data["id_room"], "channel.wubook.pms.room.type"
        )
