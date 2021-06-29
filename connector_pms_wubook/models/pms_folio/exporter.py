# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsFolioDelayedBatchExporter(Component):
    _name = "channel.wubook.pms.folio.delayed.batch.exporter"
    _inherit = "channel.wubook.delayed.batch.exporter"

    _apply_on = "channel.wubook.pms.folio"


class ChannelWubookPmsFolioDirectBatchExporter(Component):
    _name = "channel.wubook.pms.folio.direct.batch.exporter"
    _inherit = "channel.wubook.direct.batch.exporter"

    _apply_on = "channel.wubook.pms.folio"


class ChannelWubookPmsFolioExporter(Component):
    _name = "channel.wubook.pms.folio.exporter"
    _inherit = "channel.wubook.exporter"

    _apply_on = "channel.wubook.pms.folio"
