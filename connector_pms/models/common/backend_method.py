# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ChannelBackendMethod(models.Model):
    _name = "channel.backend.method"
    _description = "Channel PMS Backend Method"

    name = fields.Char(
        required=True,
    )

    backend_type_id = fields.Many2one(
        comodel_name="channel.backend.type",
        string="Backend Type",
        required=True,
        ondelete="restrict",
    )

    max_calls = fields.Integer(
        string="Max Calls",
        help="Maximum number of calls to this method in the defined time window",
    )

    time_window = fields.Integer(
        string="Time Window (seconds)",
        help="Time window in seconds",
    )

    _sql_constraints = [
        (
            "method_backend_type",
            "unique(name, backend_type_id)",
            "Only one method with the same name is allowed per Backend Type",
        ),
    ]
