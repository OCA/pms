# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
import logging
_logger = logging.getLogger(__name__)


class HotelFolio(models.Model):

    _inherit = 'hotel.folio'
