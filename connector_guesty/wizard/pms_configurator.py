# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime

from odoo import _, api, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class PMSConfigurator(models.TransientModel):
    _inherit = "pms.configurator"

    @api.constrains("start", "stop")
    def check_reservation_dates(self):
        today = datetime.now().date()
        if self.reservation_id and self.stop < self.start:
            raise ValidationError(_("'Check Out' cannot be before 'Check In'"))
        if self.reservation_id and self.start.date() < today:
            raise ValidationError(
                _(
                    "Cannot create a reservation with a 'Check In' before today ({})".format(
                        today
                    )
                )
            )

    @api.onchange("start", "stop")
    def _onchange_reservation_dates(self):
        self.check_reservation_dates()
