# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class ChannelWubookExporter(AbstractComponent):
    """ Wubook exporter for Channel """

    _name = "channel.wubook.exporter"
    _inherit = ["channel.exporter", "base.channel.wubook.connector"]

    _default_binding_field = "channel_wubook_bind_ids"


class ChannelWubookBatchExporter(AbstractComponent):
    """The role of a BatchExporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    _name = "channel.wubook.batch.exporter"
    _inherit = ["channel.batch.exporter", "base.channel.wubook.connector"]


class ChannelWubookDirectBatchExporter(AbstractComponent):
    """ Import the records directly, without delaying the jobs. """

    _name = "channel.wubook.direct.batch.exporter"
    _inherit = "channel.direct.batch.exporter"


class ChannelWubookDelayedBatchExporter(AbstractComponent):
    """ Delay import of the records """

    _name = "channel.wubook.delayed.batch.exporter"
    _inherit = "channel.delayed.batch.exporter"
