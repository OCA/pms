# Copyright (C) 2022 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StocklocationContentCheck(models.Model):
    _inherit = "stock.location.content.check"

    pms_reservation_id = fields.Many2one("pms.reservation", string="Reservation")
