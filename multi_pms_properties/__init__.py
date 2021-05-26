# Copyright 2021 Dario Lodeiros
# Copyright 2021 Eric Antones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields
from odoo.tools import config

from . import models


def _description_domain(self, env):
    if self.check_company and not self.domain:
        if self.company_dependent:
            if self.comodel_name == "res.users":
                # user needs access to current company (self.env.company)
                return "[('company_ids', 'in', allowed_company_ids[0])]"
            else:
                return "[('company_id', 'in', [allowed_company_ids[0], False])]"
        else:
            # when using check_company=True on a field on 'res.company', the
            # company_id comes from the id of the current record
            cid = "id" if self.model_name == "res.company" else "company_id"
            if self.comodel_name == "res.users":
                # User allowed company ids = user.company_ids
                return f"['|', (not {cid}, '=', True), ('company_ids', 'in', [{cid}])]"
            else:
                return f"[('company_id', 'in', [{cid}, False])]"

    if self.check_pms_properties and not self.domain:
        record = env[self.model_name]
        # Skip company_id domain to avoid domain multiproperty error in inherited views
        if (
            self.check_pms_properties
            and not self.domain
            and self.name not in ["company_id"]
        ):
            if self.model_name == "pms.property":
                prop1 = "id"
                prop2 = f"[{prop1}]"
            elif "pms_property_id" in record._fields:
                prop1 = "pms_property_id"
                prop2 = f"[{prop1}]"
            else:
                prop1 = prop2 = "pms_property_ids"
            coprop = (
                "pms_property_id"
                if "pms_property_id" in env[self.comodel_name]._fields
                else "pms_property_ids"
            )
            return f"['|', '|', \
                (not {prop1}, '=', True), \
                ('{coprop}', 'in', {prop2}), \
                ('{coprop}', '=', False)]"

    return self.domain(env[self.model_name]) if callable(self.domain) else self.domain


if "multi_pms_properties" in config.get("server_wide_modules"):
    _logger = logging.getLogger(__name__)
    _logger.info("monkey patching fields._Relational")

    fields._Relational.check_pms_properties = False
    fields._Relational._description_domain = _description_domain
