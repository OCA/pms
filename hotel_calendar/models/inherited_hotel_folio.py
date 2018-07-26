# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class HotelFolio(models.Model):
    _inherit = 'hotel.folio'

    @api.multi
    def write(self, vals):
        ret = super(HotelFolio, self).write(vals)
        if vals.get('room_lines') or vals.get('service_lines'):
            for record in self:
                record.room_lines.send_bus_notification('write', 'noshow')
        return ret
