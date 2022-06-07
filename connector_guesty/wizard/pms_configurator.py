# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime

import pytz

from odoo import _, api, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class PMSConfigurator(models.TransientModel):
    _inherit = "pms.configurator"

    @api.constrains("start", "stop")
    def check_reservation_dates(self):
        tz = pytz.timezone(self.env.user.tz)
        today = pytz.UTC.localize(datetime.now()).astimezone(tz).date()
        start_localized = pytz.UTC.localize(self.start).astimezone(tz).date()
        stop_localized = pytz.UTC.localize(self.stop).astimezone(tz).date()

        if self.reservation_id and stop_localized < start_localized:
            raise ValidationError(_("'Check Out' cannot be before 'Check In'"))
        if self.reservation_id and start_localized < today:
            raise ValidationError(
                _(
                    "Cannot create a reservation with a 'Check In' ({}) before today ({})"
                ).format(start_localized, today)
            )
