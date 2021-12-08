# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


class PmsGuestyCalendarWizard(models.TransientModel):
    _name = "pms.guesty.calendar.wizard"

    property_id = fields.Many2one("pms.property")
    start = fields.Datetime()
    stop = fields.Datetime()

    def do_action(self):
        self.env["pms.guesty.calendar"].compute_price(
            self.property_id, self.start, self.stop, None
        )
