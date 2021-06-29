# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging
import xmlrpc.client

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector_pms.components.adapter import ChannelAdapterError

_logger = logging.getLogger(__name__)


class ChannelWubookAdapter(AbstractComponent):
    _name = "channel.wubook.adapter"
    _inherit = ["channel.adapter", "base.channel.wubook.connector"]

    _id = "id"

    _date_format = "%d/%m/%Y"

    def __init__(self, environment):
        super().__init__(environment)

        self.url = self.backend_record.url
        self.username = self.backend_record.username
        self.password = self.backend_record.password
        self.apikey = self.backend_record.pkey
        self.property_code = self.backend_record.property_code

    def _exec(self, funcname, *args, pms_property=True):
        # TODO: stats and call control
        #   https://tdocs.wubook.net/wired/policies.html#anti-flood-policies
        s = xmlrpc.client.Server(self.url)
        res, token = s.acquire_token(self.username, self.password, self.apikey)
        if res:
            raise ChannelAdapterError(_("Error authorizing to endpoint. %s") % token)
        if pms_property:
            args = (self.property_code, *args)
        func = getattr(s, funcname)
        try:
            _logger.info(f"Request to Wubook: {funcname}({', '.join(map(str, args))})")
            try:
                data = func(token, *args)
                if funcname == "get_channels_info":
                    res = 0
                else:
                    res, data = data
                # DISABLEDONDEV
                # print(" ===============", data)
                # filename = f"wubook_api/wubook_{funcname}.log"
                # dnow = datetime.datetime.now(
                #     tz=pytz.timezone("Europe/Brussels")
                # ).strftime("%d-%m-%Y %H:%M:%S")
                # with open(filename, "a") as f:
                #     f.write(dnow + "\n")
                #     f.write(f"{funcname}({', '.join(map(str, args))})\n")
                #     jdata = json.dumps(data, indent=4, sort_keys=True)
                #     f.write(jdata + "\n")
                #     f.write("-----------------------------------------------------\n")
            except xmlrpc.client.Fault as e:
                if e.faultCode == 8002:
                    raise ChannelAdapterError(
                        _(
                            "Some of the resources (id's) not found on Backend "
                            "executing %s(%s). Probably they have been "
                            "deleted from the Backend"
                        )
                        % (funcname, args)
                    )
                raise
            if res:
                if funcname == "fetch_rooms_values":
                    # fetch_rooms_values(token, lcode, dfrom, dto[, rooms])
                    dfrom = datetime.datetime.strptime(
                        args[1], self._date_format
                    ).date()
                    if (datetime.date.today() - dfrom).days > 1:
                        raise ChannelAdapterError(
                            _(
                                "Error executing function %s with params %s. %s. "
                                "Wubook not allows a 'dfrom' beyond yesterday on this function"
                            )
                            % (funcname, args, data)
                        )
                raise ChannelAdapterError(
                    _("Error executing function %s with params %s. %s")
                    % (funcname, args, data)
                )
            return data
        finally:
            # TODO: reutilize token on multiple calls acoording the limits
            #   https://tdocs.wubook.net/wired/policies.html#token-limits
            res, info = s.release_token(token)
            if res:
                raise ChannelAdapterError(_("Error releasing token. %s") % info)

    def _prepare_field_type(self, field_data):
        default_values = {}
        fields = []
        for m in field_data:
            if isinstance(m, tuple):
                fields.append(m[0])
                default_values[m[0]] = m[1]
            else:
                fields.append(m)

        return fields, default_values

    def _prepare_parameters(self, values, mandatory, optional=None):
        if not optional:
            optional = []

        mandatory, mandatory_default_values = self._prepare_field_type(mandatory)
        optional, default_values = self._prepare_field_type(optional)

        default_values.update(mandatory_default_values)

        missing_fields = list(set(mandatory) - set(values))
        if missing_fields:
            raise ChannelAdapterError(_("Missing mandatory fields %s") % missing_fields)

        mandatory_values = [values[x] for x in mandatory]

        optional_values = []
        found = False
        for o in optional[::-1]:
            if not found and o in values:
                found = True
            if found:
                optional_values.append(values.get(o, default_values.get(o, False)))

        return mandatory_values + optional_values[::-1]

    def _normalize_value(self, value):
        if isinstance(value, datetime.date):
            value = value.strftime(self._date_format)
        elif isinstance(value, bool):
            value = value and 1 or 0
        elif isinstance(value, (int, str, list, tuple)):
            pass
        else:
            raise Exception("Type '%s' not supported" % type(value))
        return value

    def _domain_to_normalized_dict(self, domain, interval_fields=None):
        """Convert, if possible, standard Odoo domain to a dictionary.
        To do so it is necessary to convert all operators to
        equal '=' operator.
        """
        if not interval_fields:
            interval_fields = []
        else:
            if not isinstance(interval_fields, (tuple, list)):
                interval_fields = [interval_fields]
        res = {}
        ifields_check = {}
        for elem in domain:
            if len(elem) != 3:
                raise ValidationError(_("Wrong domain clause format %s") % elem)
            field, op, value = elem
            if op == "=":
                if field in interval_fields:
                    for postfix in ["from", "to"]:
                        field_field = "{}_{}".format(field, postfix)
                        ifields_check.setdefault(field, set())
                        if field_field in ifields_check[field]:
                            raise ValidationError(
                                _("Interval field %s duplicated") % field_field
                            )
                        ifields_check[field].add(field_field)
                        if field_field in res:
                            raise ValidationError(
                                _("Duplicated field %s") % field_field
                            )
                        res[field_field] = self._normalize_value(value)
                else:
                    if field in res:
                        raise ValidationError(_("Duplicated field %s") % field)
                    res[field] = self._normalize_value(value)
            elif op == "!=":
                if field in interval_fields:
                    raise ValidationError(
                        _("Operator {} not supported on interval fields {}").format(
                            op, field
                        )
                    )
                if not isinstance(value, bool):
                    raise ValidationError(
                        _("Not equal operation not supported for non boolean fields")
                    )
                if field in res:
                    raise ValidationError(_("Duplicated field %s") % field)
                res[field] = self._normalize_value(not value)
            elif op == "in":
                if field in interval_fields:
                    raise ValidationError(
                        _("Operator {} not supported on interval fields {}").format(
                            op, field
                        )
                    )
                if not isinstance(value, (tuple, list)):
                    raise ValidationError(
                        _("Operator '%s' only supports tuples or lists, not %s")
                        % (op, type(value))
                    )
                if field in res:
                    raise ValidationError(_("Duplicated field %s") % field)
                res[field] = self._normalize_value(value)
            elif op in (">", ">=", "<", "<="):
                if field not in interval_fields:
                    raise ValidationError(
                        _("The operator %s is only supported on interval fields") % op
                    )
                if not isinstance(
                    value, (datetime.date, datetime.datetime, int, float)
                ):
                    raise ValidationError(
                        _("Type {} not supported for operator {}").format(
                            type(value), op
                        )
                    )
                if op in (">", "<"):
                    adj = 1
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        adj = datetime.timedelta(days=adj)
                    if op == "<":
                        op, value = "<=", value - adj
                    else:
                        op, value = ">=", value + adj
                field_field = "{}_{}".format(field, op == ">=" and "from" or "to")
                ifields_check.setdefault(field, set())
                if field_field in ifields_check[field]:
                    raise ValidationError(
                        _("Interval field %s duplicated") % field_field
                    )
                ifields_check[field].add(field_field)
                if field_field in res:
                    raise ValidationError(_("Duplicated field %s") % field_field)
                res[field_field] = self._normalize_value(value)
            else:
                raise ValidationError(_("Operator %s not supported") % op)
        for field in interval_fields:
            if field in ifields_check:
                if len(ifields_check[field]) != 2:
                    raise ValidationError(
                        _(
                            "Interval field %s should have exactly 2 clauses on the domain"
                        )
                        % field
                    )
        return res

    # def _check_format_domain_search_read(self, domain):
    #     values = {}
    #     for field, op, value in domain:
    #         if re.match("^(.+_)?(dfrom|dto)$", field):
    #             if op != "=":
    #                 raise NotImplementedError(
    #                     _("Operator %s not supported for field %s") % (op, field)
    #                 )
    #             if not isinstance(value, datetime.date):
    #                 raise ValidationError(
    #                     _("Date fields must be of type date, not %s") % type(value)
    #                 )
    #             value = value.strftime(self._date_format)
    #         elif field in ("rooms", "id", "reservation_code"):
    #             if op == "=":
    #                 if not isinstance(value, int):
    #                     raise ValidationError(
    #                         _("Value should be an integer for field %s and operator %s")
    #                         % (field, op)
    #                     )
    #                 if field == "rooms":
    #                     value = [value]
    #             elif op == "in":
    #                 if not isinstance(value, (tuple, list)):
    #                     raise ValidationError(
    #                         _(
    #                             "Value should be a list of valued "
    #                             "for field %s and operator %s"
    #                         )
    #                         % (field, op)
    #                     )
    #             else:
    #                 raise NotImplementedError(
    #                     _("Operator %s not suported for field %s") % (op, field)
    #                 )
    #         elif field == 'mark':
    #             if op == "=":
    #                 value = value and 1 or 0
    #             elif op == '!=':
    #                 value = not value and 1 or 0
    #             else:
    #                 raise NotImplementedError(
    #                     _("Operator %s not supported for field %s") % (op, field)
    #                 )
    #         else:
    #             raise ValidationError(_("Unexpected field %s") % field)
    #         values[field] = value
    #     return values
