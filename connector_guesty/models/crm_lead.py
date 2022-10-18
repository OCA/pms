# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import re
import uuid

import html2text

from odoo import _, models

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
                continue
            value_list = re.findall(
                expression_id.expression_string, body_data, flags=re.MULTILINE
            )
            for value in value_list:
                custom_values[expression_id.lead_field] = str(value).strip()
                break

        if "email_from" not in custom_values:
            if msg_dict.get("email_from"):
                _email_ = msg_dict["email_from"]
                lst_mail = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", _email_)
                if lst_mail:
                    _email_ = lst_mail.group(0)

                # Todo(jorge.juarez@casai.com): found a way to have a black list
                if _email_ and (
                    "casai.com" not in _email_ and "casai.zendesk.com" not in _email_
                ):
                    custom_values["email_from"] = _email_

        if "email_from" not in custom_values:
            custom_values["email_from"] = "{}@odoo.casai.com".format(
                uuid.uuid4().hex[:13]
            )

        lead = super().message_new(msg_dict, custom_values=custom_values)
        return lead

    def action_new_quotation(self):
        # if self.partner_id and self.env.company.guesty_backend_id:
        #     action = self.action_new_quotation_reservation()
        #     action["context"] = {}
        #     action["context"]["default_crm_lead_id"] = self.id
        #     action["context"]["default_check_in"] = datetime.datetime.today()
        #     action["context"]["default_check_out"] = datetime.datetime.today()
        #     return action
        # ============ DEPRECATED ===========
        return super().action_new_quotation()

    def action_new_quotation_reservation(self):
        action = {
            "type": "ir.actions.act_window",
            "name": _("New quotation"),
            "res_model": "wiz.crm.lead.new.reservation",
            "view_mode": "form",
            "target": "new",
        }

        return action
