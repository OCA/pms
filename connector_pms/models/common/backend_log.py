# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ChannelBackendLog(models.Model):
    _name = "channel.backend.log"
    _order = "timestamp desc"
    _description = "Channel PMS Backend API Log"

    backend_id = fields.Many2one(
        comodel_name="channel.backend",
        string="Backend",
        required=True,
        readonly=True,
        ondelete="restrict",
    )

    timestamp = fields.Datetime(
        string="Timestamp",
        required=True,
        readonly=True,
    )

    method_id = fields.Many2one(
        comodel_name="channel.backend.method",
        string="Method",
        required=True,
        readonly=True,
        ondelete="restrict",
    )

    arguments = fields.Text(
        string="Arguments",
        required=True,
        readonly=True,
    )
    response_code = fields.Text(
        string="Response Code",
        required=True,
        readonly=True,
    )
    response = fields.Text(
        string="Response",
        required=True,
        readonly=True,
    )
