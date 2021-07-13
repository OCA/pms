# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# from odoo.addons.queue_job.job import job, related_action


class ChannelBinding(models.AbstractModel):
    _name = "channel.binding"
    _inherit = "external.binding"
    _description = "Channel PMS Binding (abstract)"

    external_id = fields.Integer(string="External ID", required=False)

    # by default we consider sync_date as the import one
    sync_date = fields.Datetime(readonly=True, string="Last Sync (import)")
    sync_date_export = fields.Datetime(readonly=True, string="Last Sync (export)")

    # TODO: move next 2 fields to external.binding in order to
    #   add this functionality to connector
    actual_write_date = fields.Datetime(
        string="Last Updated on (actual)",
        help="Max write date between binding and actual record",
        compute="_compute_actual_write_date",
        readonly=True,
    )

    @api.depends("write_date", "odoo_id.write_date")
    def _compute_actual_write_date(self):
        for rec in self:
            rec.actual_write_date = max(rec.write_date, rec.odoo_id.write_date).replace(
                microsecond=0
            )

    # We don't need synced attribute for import since we'd need to know the
    # remote modification date not the local one
    synced_export = fields.Boolean(
        string="Synced (export)", compute="_compute_synced_export", readonly=True
    )

    @api.depends("sync_date_export", "actual_write_date")
    def _compute_synced_export(self):
        for rec in self:
            rec.synced_export = (
                rec.sync_date_export and rec.sync_date_export >= rec.actual_write_date
            )

    _sql_constraints = [
        (
            "channel_external_uniq",
            "unique(backend_id, external_id)",
            "A binding already exists with the same External (Channel) ID.",
        ),
        (
            "channel_internal_uniq",
            "unique(backend_id, odoo_id)",
            "A binding already exists with the same Internal (Odoo) ID.",
        ),
    ]

    # default methods
    @api.model
    def import_data(self, backend_record=None):
        """ Prepare the batch import of records from Channel """
        return self.import_batch(backend_record=backend_record)

    @api.model
    def export_data(self, backend_record=None):
        """ Prepare the batch export records to Channel """
        return self.export_batch(backend_record=backend_record)

    # syncronizer import
    @api.model
    def import_batch(self, backend_record, domain=None, delayed=True):
        """ Prepare the batch import of records modified on Channel """
        if not domain:
            domain = []
        with backend_record.work_on(self._name) as work:
            importer = work.component(
                usage=delayed and "delayed.batch.importer" or "direct.batch.importer"
            )
            return importer.run(domain=domain)

    @api.model
    def import_record(self, backend_record, external_id, external_data=None):
        """ Import Channel record """
        if not external_data:
            external_data = {}
        with backend_record.work_on(self._name) as work:
            importer = work.component(usage="direct.record.importer")
            return importer.run(external_id, external_data=external_data)

    # syncronizer export
    @api.model
    def export_batch(self, backend_record, domain=None, delayed=True):
        """ Prepare the batch export of records modified on Odoo """
        if not domain:
            domain = []
        with backend_record.work_on(self._name) as work:
            exporter = work.component(
                usage=delayed and "delayed.batch.exporter" or "direct.batch.exporter"
            )
            return exporter.run(domain=domain)

    @api.model
    def export_record(self, backend_record, relation):
        """ Export Odoo record """
        with backend_record.work_on(self._name) as work:
            exporter = work.component(usage="direct.record.exporter")
            return exporter.run(relation)

    # existing binding synchronization
    def resync_import(self):
        for record in self:
            with record.backend_id.work_on(record._name) as work:
                binder = work.component(usage="binder")
                external_id = binder.to_external(record)

            func = record.import_record
            if record.env.context.get("connector_delay"):
                func = func.with_delay

            func(record.backend_id, external_id)

        return True

    def resync_export(self):
        for record in self:
            with record.backend_id.work_on(record._name) as work:
                binder = work.component(usage="binder")
                relation = binder.unwrap_binding(record)

            func = record.export_record
            if record.env.context.get("connector_delay"):
                func = func.with_delay

            func(record.backend_id, relation)

        return True
