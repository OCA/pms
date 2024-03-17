# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ChannelBackend(models.Model):
    _name = "channel.backend"
    _description = "Channel PMS Backend"

    name = fields.Char("Name", required=True)

    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        required=True,
        ondelete="restrict",
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        ondelete="restrict",
    )

    backend_type_id = fields.Many2one(
        string="Type",
        comodel_name="channel.backend.type",
        required=True,
        ondelete="restrict",
    )

    export_disabled = fields.Boolean(string="Export Disabled")

    @property
    def child_id(self):
        self.ensure_one()
        # TODO: move to computed field
        model = self.env[self.backend_type_id.model_type_id.model]._main_model
        child_backends = self.env[model].search(
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

    def channel_config(self):
        self.ensure_one()
        # TODO: move to computed field
        model = self.env[self.backend_type_id.model_type_id.model]._main_model
        return {
            "type": "ir.actions.act_window",
            "res_model": model,
            "views": [[False, "form"]],
            "context": not self.child_id and {"default_parent_id": self.id},
            "res_id": self.child_id.id,
        }
