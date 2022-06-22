# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import models

_log = logging.getLogger(__name__)


class PmsConfigurator(models.TransientModel):
    _inherit = "pms.configurator"
