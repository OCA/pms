# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class ChannelExporter(AbstractComponent):
    """ Base exporter for Channel """

    _name = "channel.exporter"
    _inherit = "generic.exporter.custom"

    _usage = "direct.record.exporter"


class ChannelBatchExporter(AbstractComponent):
    """The role of a BatchExporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    _name = "channel.batch.exporter"
    _inherit = "base.exporter"

    def run(self, domain=None):
        """ Run the batch synchronization """
        if not domain:
            domain = []
        relation_model = self.binder_for(self.model._name).unwrap_model()
        for relation in self.env[relation_model].search(domain):
            self._export_record(relation)

    def _export_record(self, external_id):
        """Export a record directly or delay the export of the record.

        Method to implement in sub-classes.
        """
        raise NotImplementedError


class ChannelDirectBatchExporter(AbstractComponent):
    """ Import the records directly, without delaying the jobs. """

    _name = "channel.direct.batch.exporter"
    _inherit = "channel.batch.exporter"

    _usage = "direct.batch.exporter"

    def _export_record(self, relation):
        """ export the record directly """
        self.model.export_record(self.backend_record, relation)


class ChannelDelayedBatchExporter(AbstractComponent):
    """ Delay import of the records """

    _name = "channel.delayed.batch.exporter"
    _inherit = "channel.batch.exporter"

    _usage = "delayed.batch.exporter"

    def _export_record(self, relation, job_options=None):
        """ Delay the export of the records"""
        delayable = self.model.with_delay(**job_options or {})
        delayable.export_record(self.backend_record, relation)
