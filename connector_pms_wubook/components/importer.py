# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class ChannelWubookImporter(AbstractComponent):
    """ Wubook importer for Channel """

    _name = "channel.wubook.importer"
    _inherit = ["channel.importer", "base.channel.wubook.connector"]


class ChannelWubookBatchImporter(AbstractComponent):
    """The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    _name = "channel.wubook.batch.importer"
    _inherit = ["channel.batch.importer", "base.channel.wubook.connector"]


class ChannelWubookDirectBatchImporter(AbstractComponent):
    """ Import the records directly, without delaying the jobs. """

    _name = "channel.wubook.direct.batch.importer"
    _inherit = "channel.direct.batch.importer"


class ChannelWubookDelayedBatchImporter(AbstractComponent):
    """ Delay import of the records """

    _name = "channel.wubook.delayed.batch.importer"
    _inherit = "channel.delayed.batch.importer"
