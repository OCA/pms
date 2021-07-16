# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    def wubook_import_record_related_action(self, name):
        self.ensure_one()
        backend_record, external_id = self.args[:2]

        with backend_record.work_on(self.model_name) as work:
            binder = work.component(usage="binder")
            relation = binder.to_internal(external_id, unwrap=True)

        action = {
            "name": name,
            "type": "ir.actions.act_window",
            "res_model": relation._name,
            "view_type": "form",
            "view_mode": "form",
            "res_id": relation.id,
        }

        return action

    def wubook_export_record_related_action(self, name):
        self.ensure_one()
        model = self.model_name
        partner = self.records
        action = {
            "name": name,
            "type": "ir.actions.act_window",
            "res_model": model,
            "view_type": "form",
            "view_mode": "form",
            "res_id": partner.id,
        }
        return action
