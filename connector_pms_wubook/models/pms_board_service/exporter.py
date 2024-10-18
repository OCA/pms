# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsBoardServiceDelayedBatchExporter(Component):
    _name = "channel.wubook.pms.board.service.delayed.batch.exporter"
    _inherit = "channel.wubook.delayed.batch.exporter"

    _apply_on = "channel.wubook.pms.board.service"


class ChannelWubookPmsBoardServiceDirectBatchExporter(Component):
    _name = "channel.wubook.pms.board.service.direct.batch.exporter"
    _inherit = "channel.wubook.direct.batch.exporter"

    _apply_on = "channel.wubook.pms.board.service"


class ChannelWubookPmsBoardServiceExporter(Component):
    _name = "channel.wubook.pms.board.service.exporter"
    _inherit = "channel.wubook.exporter"

    _apply_on = "channel.wubook.pms.board.service"
