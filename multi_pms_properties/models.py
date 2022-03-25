# Copyright 2021 Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class BaseModel(models.AbstractModel):
    _inherit = "base"
    _check_pms_properties_auto = False
    """On write and create, call ``_check_pms_properties_auto`` to ensure properties
    consistency on the relational fields having ``check_pms_properties=True``
    as attribute.
    """

    def _valid_field_parameter(self, field, name):
        """Make new field attribute valid for Odoo."""
        return name == "check_pms_properties" or super()._valid_field_parameter(
            field, name
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(BaseModel, self).create(vals_list)
        if self._check_pms_properties_auto:
            records._check_pms_properties()
        return records

    def write(self, vals):
        res = super(BaseModel, self).write(vals)
        check_pms_properties = False
        for fname in vals:
            field = self._fields.get(fname)
            if (
                fname == "pms_property_id"
                or fname == "pms_property_ids"
                or fname == "company_id"
                or (field.relational and getattr(field, "check_pms_properties", False))
            ):
                check_pms_properties = True
        if res and check_pms_properties and self._check_pms_properties_auto:
            self._check_pms_properties()
        return res

    def _check_pms_properties(self, fnames=None):
        """Check the properties of the values of the given field names.

        :param list fnames: names of relational fields to check
        :raises UserError: if the `pms_properties` of the value of any field is not
            in `[False, self.pms_property_id]` (or `self` if
            :class:`~odoo.addons.base.models.pms_property`).

        For :class:`~odoo.addons.base.models.res_users` relational fields,
        verifies record company is in `company_ids` fields.

        User with main pms property A, having access to pms property A and B, could be
        assigned or linked to records in property B.
        """
        if fnames is None:
            fnames = self._fields

        regular_fields = self._get_regular_fields(fnames)

        if not regular_fields:
            return

        inconsistencies = self._check_inconsistencies(regular_fields)

        if inconsistencies:
            lines = [_("Incompatible properties on records:")]
            property_msg = _(
                """- Record is properties %(pms_properties)r and %(field)r
                (%(fname)s: %(values)s) belongs to another properties."""
            )
            record_msg = _(
                """- %(record)r belongs to properties %(pms_properties)r and
                %(field)r (%(fname)s: %(values)s) belongs to another properties."""
            )
            for record, name, corecords in inconsistencies[:5]:
                if record._name == "pms.property":
                    msg, pms_properties = property_msg, record
                else:
                    msg, pms_properties = (
                        record_msg,
                        record.pms_property_id.name
                        if "pms_property_id" in record
                        else ", ".join(repr(p.name) for p in record.pms_property_ids),
                    )
                field = self.env["ir.model.fields"]._get(self._name, name)
                lines.append(
                    msg
                    % {
                        "record": record.display_name,
                        "pms_properties": pms_properties,
                        "field": field.field_description,
                        "fname": field.name,
                        "values": ", ".join(
                            repr(rec.display_name) for rec in corecords
                        ),
                    }
                )
            raise UserError("\n".join(lines))

    def _get_regular_fields(self, fnames):
        regular_fields = []
        for name in fnames:
            field = self._fields[name]
            if (
                field.relational
                and getattr(field, "check_pms_properties", False)
                and (
                    "pms_property_id" in self.env[field.comodel_name]
                    or "pms_property_ids" in self.env[field.comodel_name]
                )
            ):
                regular_fields.append(name)
        return regular_fields

    def _check_inconsistencies(self, regular_fields):
        inconsistencies = []
        for record in self:
            pms_properties = False
            if record._name == "pms.property":
                pms_properties = record
            if "pms_property_id" in record:
                pms_properties = record.pms_property_id
            if "pms_property_ids" in record:
                pms_properties = record.pms_property_ids
            # Check the property & company consistence
            if "company_id" in self._fields:
                if record.company_id and pms_properties:
                    property_companies = pms_properties.mapped("company_id.id")
                    if (
                        len(property_companies) > 1
                        or record.company_id.id != property_companies[0]
                    ):
                        raise UserError(
                            _(
                                "You cannot establish a company other than "
                                "the one with the established properties"
                            )
                        )
            # Check verifies that all
            # records linked via relation fields are compatible
            # with the properties of the origin document,
            for name in regular_fields:
                field = self._fields[name]
                co_pms_properties = False

                corecord = record.sudo()[name]
                # TODO:res.users management properties
                if "pms_property_id" in corecord:
                    co_pms_properties = corecord.pms_property_id
                if "pms_property_ids" in corecord:
                    co_pms_properties = corecord.pms_property_ids
                if (
                    # There is an inconsistency if:
                    #
                    # - Record has properties and corecord too and
                    # there's no match between them:
                    # X  Pms_room_class with Property1 cannot contain
                    #                       Pms_room with property2   X
                    #
                    # - Record has a relation one2many with corecord and
                    # corecord properties aren't included in record properties
                    # or what is the same, subtraction between corecord properties
                    # and record properties must be False:
                    #  X  Pricelist with Prop1 and Prop2 cannot contain
                    #                   Pricelist_item with Prop1 and Prop3  X
                    #  X  Pricelist with Prop1 and Prop2 cannot contain
                    #                   Pricelist_item with Prop1, Prop2 and Prop3  X
                    # -In case that record has a relation many2one
                    #                   with corecord the condition is the same as avobe
                    (
                        pms_properties
                        and co_pms_properties
                        and (not pms_properties & co_pms_properties)
                    )
                    or (
                        corecord
                        and field.type == "one2many"
                        and pms_properties
                        and (co_pms_properties - pms_properties)
                    )
                    or (
                        field.type == "many2one"
                        and co_pms_properties
                        and ((pms_properties - co_pms_properties) or not pms_properties)
                    )
                ):
                    inconsistencies.append((record, name, corecord))
        return inconsistencies
