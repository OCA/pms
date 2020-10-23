# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from contextlib import contextmanager

import psycopg2

from odoo import _

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.exception import IDMissingInBackend, RetryableJobError

_logger = logging.getLogger(__name__)


class GenericExporterCustom(AbstractComponent):
    """ Generic Synchronizer for exporting data from Odoo to a backend """

    _name = "generic.exporter.custom"
    _inherit = "base.exporter"

    _default_binding_field = None

    def __init__(self, working_context):
        super(GenericExporterCustom, self).__init__(working_context)
        self.binding = None
        self.external_id = None

    def _should_import(self):
        return False

    def _delay_import(self):
        """Schedule an import of the record.

        Adapt in the sub-classes when the model is not imported
        using ``import_record``.
        """
        # force is True because the sync_date will be more recent
        # so the import would be skipped
        assert self.external_id
        self.binding.with_delay().import_record(
            self.backend_record, self.external_id, force=True
        )

    def _mapper_options(self):
        return {"binding": self.binding}

    def run(self, relation, *args, **kwargs):
        """Run the synchronization

        :param binding: binding record to export
        """
        # get binding from real record
        self.binding = self.binder.wrap_record(relation)

        # if not binding, try to link to existing external record with
        # the same alternate key and create/update binding
        if not self.binding or not self.binding.external_id:
            self.binding = (
                self.binder.to_binding_from_internal_key(relation) or self.binding
            )

        # if still not binding, create an empty one
        if not self.binding:
            self.binding = self.binder.wrap_record(relation, force=True)

        self.external_id = self.binder.to_external(self.binding)

        try:
            should_import = self._should_import()
        except IDMissingInBackend:
            self.external_id = None
            should_import = False
        if should_import:
            self._delay_import()

        result = self._run(*args, **kwargs)

        self.binder.bind(self.external_id, self.binding)
        # Commit so we keep the external ID when there are several
        # exports (due to dependencies) and one of them fails.
        # The commit will also release the lock acquired on the binding
        # record
        # if not odoo.tools.config["test_enable"]:
        #     self.env.cr.commit()  # pylint: disable=E8102

        self._after_export()
        return result

    def _run(self, internal_fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding

        if not self.external_id:
            internal_fields = None  # should be created with all the fields

        if self._has_to_skip():
            return

        # export the missing linked resources
        self._export_dependencies()

        # prevent other jobs to export the same record
        # will be released on commit (or rollback)
        self._lock()

        map_record = self._map_data()

        # passing info to the mapper
        opts = self._mapper_options()

        if self.external_id:
            values = self._update_data(map_record, fields=internal_fields, **opts)
            if not values:
                return _("Nothing to export.")
            self._update(values)
        else:
            values = self._create_data(map_record, fields=internal_fields, **opts)
            if not values:
                return _("Nothing to export.")
            self.external_id = self._create(values)

        return _("Record exported with ID %s on Backend.") % self.external_id

    def _after_export(self):
        """ Can do several actions after exporting a record on the backend """

    def _lock(self):
        """Lock the binding record.

        Lock the binding record so we are sure that only one export
        job is running for this record if concurrent jobs have to export the
        same record.

        When concurrent jobs try to export the same record, the first one
        will lock and proceed, the others will fail to lock and will be
        retried later.

        This behavior works also when the export becomes multilevel
        with :meth:`_export_dependencies`. Each level will set its own lock
        on the binding record it has to export.

        """
        sql = "SELECT id FROM %s WHERE ID = %%s FOR UPDATE NOWAIT" % self.model._table
        try:
            self.env.cr.execute(sql, (self.binding.id,), log_exceptions=False)
        except psycopg2.OperationalError:
            _logger.info(
                "A concurrent job is already exporting the same "
                "record (%s with id %s). Job delayed later.",
                self.model._name,
                self.binding.id,
            )
            raise RetryableJobError(
                "A concurrent job is already exporting the same record "
                "(%s with id %s). The job will be retried later."
                % (self.model._name, self.binding.id)
            )

    def _has_to_skip(self):
        """ Return True if the export can be skipped """
        return False

    @contextmanager
    def _retry_unique_violation(self):
        """Context manager: catch Unique constraint error and retry the
        job later.

        When we execute several jobs workers concurrently, it happens
        that 2 jobs are creating the same record at the same time (binding
        record created by :meth:`_export_dependency`), resulting in:

            IntegrityError: duplicate key value violates unique
            constraint "my_backend_product_product_odoo_uniq"
            DETAIL:  Key (backend_id, odoo_id)=(1, 4851) already exists.

        In that case, we'll retry the import just later.

        .. warning:: The unique constraint must be created on the
                     for the same External record.

        """
        try:
            yield
        except psycopg2.IntegrityError as err:
            if err.pgcode == psycopg2.errorcodes.UNIQUE_VIOLATION:
                raise RetryableJobError(
                    "A database error caused the failure of the job:\n"
                    "%s\n\n"
                    "Likely due to 2 concurrent jobs wanting to create "
                    "the same record. The job will be retried later." % err
                )
            else:
                raise

    def _export_dependency(
        self,
        relation,
        binding_model,
        component_usage="direct.record.exporter",
        binding_field=None,
        binding_extra_vals=None,
        always=False,
    ):
        """
        Export a dependency. The exporter class is a subclass of
        ``GenericExporter``. If a more precise class need to be defined,
        it can be passed to the ``exporter_class`` keyword argument.

        .. warning:: a commit is done at the end of the export of each
                     dependency. The reason for that is that we pushed a record
                     on the backend and we absolutely have to keep its ID.

                     So you *must* take care not to modify the Odoo
                     database during an export, excepted when writing
                     back the external ID or eventually to store
                     external data that we have to keep on this side.

                     You should call this method only at the beginning
                     of the exporter synchronization,
                     in :meth:`~._export_dependencies`.

        :param relation: record to export if not already exported
        :type relation: :py:class:`odoo.models.BaseModel`
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param component_usage: 'usage' to look for to find the Component to
                                for the export, by default 'record.exporter'
        :type exporter: str | unicode
        :param binding_field: name of the one2many field on a normal
                              record that points to the binding record
                              (default: my_backend_bind_ids).
                              It is used only when the relation is not
                              a binding but is a normal record.
        :type binding_field: str | unicode
        :binding_extra_vals:  In case we want to create a new binding
                              pass extra values for this binding
        :type binding_extra_vals: dict
        """
        if not relation:
            return

        binding = None
        if not always:
            rel_binder = self.binder_for(binding_model)
            binding = rel_binder.wrap_record(relation)
            if not binding or not binding.external_id:
                binding = rel_binder.to_binding_from_internal_key(relation)

        if always or not binding:
            exporter = self.component(usage=component_usage, model_name=binding_model)
            exporter.run(relation)

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        return

    def _map_data(self):
        """Returns an instance of
        :py:class:`~odoo.addons.connector.components.mapper.MapRecord`

        """
        return self.mapper.map_record(self.binding)

    def _validate_create_data(self, data):
        """Check if the values to import are correct

        Pro-actively check before the ``Model.create`` if some fields
        are missing or invalid

        Raise `InvalidDataError`
        """
        return

    def _validate_update_data(self, data):
        """Check if the values to import are correct

        Pro-actively check before the ``Model.update`` if some fields
        are missing or invalid

        Raise `InvalidDataError`
        """
        return

    def _create_data(self, map_record, fields=None, **kwargs):
        """ Get the data to pass to :py:meth:`_create` """
        return map_record.values(for_create=True, fields=fields, **kwargs)

    def _create(self, data):
        """ Create the External record """
        # special check on data before export
        self._validate_create_data(data)
        # DISABLEDONDEV
        print(">>>>>>>>>>>>>>CREATE", data)
        if self.model._name in (
            "channel.wubook.pms.availability",
            # "channel.wubook.pms.availability.plan",
        ):
            return self.backend_adapter.create(data)
        # raise Exception("Unexpected Create!!")
        # return self.backend_adapter.create(data)

    def _update_data(self, map_record, fields=None, **kwargs):
        """ Get the data to pass to :py:meth:`_update` """
        return map_record.values(fields=fields, **kwargs)

    def _update(self, data):
        """ Update an External record """
        assert self.external_id
        # special check on data before export
        self._validate_update_data(data)
        # DISABLEDONDEV
        print(">>>>>>>>>>>>>>WRITE", data)
        # if self.model._name in ("channel.wubook.pms.availability.plan",):
        #     self.backend_adapter.write(self.external_id, data)
        # raise Exception("Unexpected Write!!")
        # self.backend_adapter.write(self.external_id, data)
