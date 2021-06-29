# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ChannelWubookBackendTypeBoardService(models.Model):
    _name = "channel.wubook.backend.type.board.service"
    _description = "Channel Wubook PMS Backend Type Board services Map"

    backend_type_id = fields.Many2one(
        comodel_name="channel.wubook.backend.type",
        required=True,
        ondelete="cascade",
    )

    wubook_board_service = fields.Selection(
        string="Wubook Board Service",
        required=True,
        selection=[
            # ("nb", "No Board"), # no board means without any board service
            ("bb", "Breakfast"),
            ("hb", "Half Board"),
            ("fb", "Full Board"),
            ("ai", "All Inclusive"),
        ],
    )

    board_service_shortname = fields.Char(
        string="Wubook Board Service Shortname",
    )

    _sql_constraints = [
        (
            "uniq",
            "unique(backend_type_id,wubook_board_service,board_service_shortname)",
            "Board Service and Shortname already used in another map line",
        ),
        (
            "board_service_uniq",
            "unique(backend_type_id,wubook_board_service)",
            "Board Service already used in another map line",
        ),
        (
            "board_service_shortname_uniq",
            "unique(backend_type_id,board_service_shortname)",
            "Shortname already used in another map line",
        ),
    ]
