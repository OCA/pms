# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    ota_reservation_code = fields.Char(
        string="OTA Reservation Code",
        readonly=True,
    )

    @api.depends("ota_reservation_code")
    def _compute_external_reference(self):
        super(PmsReservation, self)._compute_external_reference()

    def _get_reservation_external_reference(self):
        reference = super(PmsReservation, self)._get_reservation_external_reference()
        if self.ota_reservation_code:
            reference = self.ota_reservation_code
        return reference
