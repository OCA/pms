# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class QueueJob(models.Model):
    _inherit = "queue.job"

    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        store=True,
    )

    @api.depends("args")
    def _compute_pms_property_id(self):
        for rec in self:
            if rec.args[1:2] and isinstance(
                rec.args[1:2][0], type(self.env["pms.property"])
            ):
                rec.pms_property_id = rec.args[1:2][0]
            else:
                rec.pms_property_id = False
