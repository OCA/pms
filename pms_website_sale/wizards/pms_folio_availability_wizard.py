# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AvailabilityWizard(models.TransientModel):
    _inherit = "pms.folio.availability.wizard"
