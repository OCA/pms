# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import AbstractComponent


class ChannelAdapter(AbstractComponent):
    _name = "channel.adapter"
    _inherit = "base.backend.adapter.crud"

    def chunks(self, l, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(l), n):
            yield l[i : i + n]

    def _filter(self, values, domain=None):
        # TODO support for domains with 'or' clauses
        # TODO refactor and optimize
        if not domain:
            return values

        values_filtered = []
        for record in values:
            for elem in domain:
                k, op, v = elem
                if k not in record:
                    raise ValidationError(_("Key %s does not exist") % k)
                if op == "=":
                    if record[k] != v:
                        break
                elif op == "!=":
                    if record[k] == v:
                        break
                elif op == ">":
                    if record[k] <= v:
                        break
                elif op == "<":
                    if record[k] >= v:
                        break
                elif op == ">=":
                    if record[k] < v:
                        break
                elif op == "<=":
                    if record[k] > v:
                        break
                elif op == "in":
                    if not isinstance(v, (tuple, list)):
                        raise ValidationError(
                            _("The value %s should be a list or tuple") % v
                        )
                    if record[k] not in v:
                        break
                elif op == "not in":
                    if not isinstance(v, (tuple, list)):
                        raise ValidationError(
                            _("The value %s should be a list or tuple") % v
                        )
                    if record[k] in v:
                        break
                else:
                    raise NotImplementedError("Operator '%s' not supported" % op)
            else:
                values_filtered.append(record)

        return values_filtered

    def _extract_domain_clauses(self, domain, fields):
        if not isinstance(fields, (tuple, list)):
            fields = [fields]
        extracted, rest = [], []
        for clause in domain:
            tgt = extracted if clause[0] in fields else rest
            tgt.append(clause)
        return extracted, rest

    def _convert_format(self, elem, mapper, path=""):
        if isinstance(elem, dict):
            for k, v in elem.items():
                current_path = "{}/{}".format(path, k)
                if v == "":
                    elem[k] = None
                    continue
                if isinstance(v, (tuple, list, dict)):
                    if isinstance(v, dict):
                        if current_path in mapper:
                            v2 = {}
                            for k1, v1 in v.items():
                                new_value = mapper[current_path](k1)
                                v2[new_value] = v1
                            v = elem[k] = v2
                    self._convert_format(v, mapper, current_path)
                elif isinstance(
                    v, (str, int, float, bool, datetime.date, datetime.datetime)
                ):
                    if current_path in mapper:
                        elem[k] = mapper[current_path](v)
                else:
                    raise NotImplementedError("Type %s not implemented" % type(v))
        elif isinstance(elem, (tuple, list)):
            for ch in elem:
                self._convert_format(ch, mapper, path)
        elif isinstance(
            elem, (str, int, float, bool, datetime.date, datetime.datetime)
        ):
            pass
        else:
            raise NotImplementedError("Type %s not implemented" % type(elem))


class ChannelAdapterError(Exception):
    def __init__(self, message, data=None):
        super().__init__(message)
        self.data = data or {}
