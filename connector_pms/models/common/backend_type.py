# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ChannelBackendType(models.Model):
    _name = "channel.backend.type"
    _description = "Channel PMS Backend Type"

    name = fields.Char("Name", required=True)

    model_type_id = fields.Many2one(
        comodel_name="ir.model",
        string="Referenced Model Type",
        required=True,
        ondelete="cascade",
        domain=lambda self: [
            ("model", "in", self._get_channel_backend_type_model_names())
        ],
    )

    @property
    def child_id(self):
        self.ensure_one()
        child_backends = self.env[self.model_type_id.model].search(
            [
                ("parent_id", "=", self.id),
            ]
        )
        if len(child_backends) > 1:
            raise ValidationError(
                _(
                    "Inconsistency detected. More than one "
                    "backend's child found for the same parent"
                )
            )
        return child_backends

    @api.model
    def _get_channel_backend_type_model_names(self):
        res = []
        return res

    def channel_type_config(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.model_type_id.model,
            "views": [[False, "form"]],
            "context": not self.child_id and {"default_parent_id": self.id},
            "res_id": self.child_id.id,
        }
