# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsRoomTypeClassDelayedBatchImporter(Component):
    _name = "channel.wubook.pms.room.type.class.delayed.batch.importer"
    _inherit = "channel.wubook.delayed.batch.importer"

    _apply_on = "channel.wubook.pms.room.type.class"


class ChannelWubookPmsRoomTypeClassDirectBatchImporter(Component):
    _name = "channel.wubook.pms.room.type.class.direct.batch.importer"
    _inherit = "channel.wubook.direct.batch.importer"

    _apply_on = "channel.wubook.pms.room.type.class"


class ChannelWubookPmsRoomTypeClassImporter(Component):
    _name = "channel.wubook.pms.room.type.class.importer"
    _inherit = "channel.wubook.importer"

    _apply_on = "channel.wubook.pms.room.type.class"
