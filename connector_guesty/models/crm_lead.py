# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import re
import uuid

import html2text

from odoo import models

_log = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    def message_new(self, msg_dict, custom_values=None):
        # add a custom behavior when receiving a new lead through the mail's gateway
        custom_values = custom_values or {}
        if custom_values.get("type", "not_defined") not in ["lead", "opportunity"]:
            return super().message_new(msg_dict, custom_values=custom_values)

        body_data = msg_dict.get("body", str())
        body_data = html2text.html2text(body_data)
        expression_ids = self.env["crm.lead.rule"].sudo().search([])
        for expression_id in expression_ids:
            _log.info(expression_id.expression_string)
            if expression_id.lead_field in custom_values:
                break
            value_list = re.findall(
                expression_id.expression_string, body_data, flags=re.MULTILINE
            )
            for value in value_list:
                custom_values[expression_id.lead_field] = str(value).strip()
                break

        if "email_from" not in custom_values:
            custom_values["email_from"] = "{}@odoo.casai.com".format(
                uuid.uuid4().hex[:13]
            )

        lead = super().message_new(msg_dict, custom_values=custom_values)
        return lead
