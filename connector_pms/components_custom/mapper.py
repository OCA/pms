# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import collections
import logging

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import m2o_to_external

_logger = logging.getLogger(__name__)


class Mapper(AbstractComponent):
    _inherit = "base.mapper"

    def _apply_with_options(self, map_record):
        """
        Hack to allow having non required children field
        """
        assert (
            self.options is not None
        ), "options should be defined with '_mapping_options'"
        _logger.debug("converting record %s to model %s", map_record.source, self.model)

        fields = self.options.fields
        for_create = self.options.for_create
        result = {}
        for from_attr, to_attr in self.direct:
            if isinstance(from_attr, collections.Callable):
                attr_name = self._direct_source_field_name(from_attr)
            else:
                attr_name = from_attr

            if not fields or attr_name in fields:
                value = self._map_direct(map_record.source, from_attr, to_attr)
                result[to_attr] = value

        for meth, definition in self.map_methods:
            mapping_changed_by = definition.changed_by
            if not fields or (
                mapping_changed_by and mapping_changed_by.intersection(fields)
            ):
                if definition.only_create and not for_create:
                    continue
                values = meth(map_record.source)
                if not values:
                    continue
                if not isinstance(values, dict):
                    raise ValueError(
                        "%s: invalid return value for the "
                        "mapping method %s" % (values, meth)
                    )
                result.update(values)

        for from_attr, to_attr, model_name in self.children:
            if not fields or from_attr in fields:
                if from_attr in map_record.source:
                    result[to_attr] = self._map_child(
                        map_record, from_attr, to_attr, model_name
                    )

        return self.finalize(map_record, result)

    def get_target_fields(self, map_record, fields):
        if not fields:
            return []
        fields = set(fields)
        result = {}
        for from_attr, to_attr in self.direct:
            if isinstance(from_attr, collections.Callable):
                # attr_name = self._direct_source_field_name(from_attr)
                # TODO
                raise NotImplementedError
            else:
                if to_attr in fields:
                    if to_attr in result:
                        raise ValidationError(_("Field '%s' mapping defined twice"))
                    result[to_attr] = from_attr

        # TODO: create a new decorator to write the field mapping manually
        # for meth, definition in self.map_methods:
        #     for mcb in definition.mapping:
        #         if mcb in fields:
        #             if to_attr in result:
        #                 raise ValidationError("Field '%s' mapping defined twice")
        #             result[to_attr] = from_attr

        for from_attr, to_attr, _model_name in self.children:
            if to_attr in fields:
                if to_attr in result:
                    raise ValidationError(_("Field '%s' mapping defined twice"))
                result[to_attr] = from_attr

        return list(set(result.values()))


class ChannelChildMapperImport(AbstractComponent):
    _inherit = "base.map.child"

    def get_all_items(self, mapper, items, parent, to_attr, options):
        mapped = []
        for item in items:
            map_record = mapper.map_record(item, parent=parent)
            if self.skip_item(map_record):
                continue
            item_values = self.get_item_values(map_record, to_attr, options)
            if item_values:
                mapped.append(item_values)
        return mapped

    def get_items(self, items, parent, to_attr, options):
        mapper = self._child_mapper()
        mapped = self.get_all_items(mapper, items, parent, to_attr, options)
        return self.format_items(mapped)


# TODO: create a fix on OCA repo and remove this class
class ExportMapper(AbstractComponent):
    _inherit = "base.export.mapper"

    def _map_direct(self, record, from_attr, to_attr):
        """Apply the ``direct`` mappings.

        :param record: record to convert from a source to a target
        :param from_attr: name of the source attribute or a callable
        :type from_attr: callable | str
        :param to_attr: name of the target attribute
        :type to_attr: str
        """
        if isinstance(from_attr, collections.Callable):
            return from_attr(self, record, to_attr)

        value = record[from_attr]
        if value is None:  # we need to allow fields with value 0
            return False

        # Backward compatibility: when a field is a relation, and a modifier is
        # not used, we assume that the relation model is a binding.
        # Use an explicit modifier m2o_to_external  in the 'direct' mappings to
        # change that.
        field = self.model._fields[from_attr]
        if field.type == "many2one":
            mapping_func = m2o_to_external(from_attr)
            value = mapping_func(self, record, to_attr)
        return value
