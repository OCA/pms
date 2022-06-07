# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_log = logging.getLogger(__name__)


class PmsGuestyReservation(models.Model):
    _name = "pms.guesty.reservation"
    _description = "PMS Guesty reservation"
    _rec_name = "uuid"

    @api.depends("uuid", "state")
    def _compute_display_name(self):
        self.display_name = "{} - {}".format(self.state, self.uuid)

    uuid = fields.Char(copy=False)
    state = fields.Char(copy=False, default="inquiry")

    _sql_constraints = [
        (
            "unique_uuid",
            "unique(uuid)",
            "Reservation UUID cannot be duplicated",
        )
    ]
