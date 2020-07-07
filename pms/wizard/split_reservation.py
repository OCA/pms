# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta
from openerp.exceptions import ValidationError
from openerp import models, fields, api, _
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)


class SplitReservationWizard(models.TransientModel):
    _name = 'pms.wizard.split.reservation'

    nights = fields.Integer('Nights', default=1, min=1)

    @api.multi
    def split_reservation(self):
        reservation_id = self.env['pms.reservation'].browse(
            self.env.context.get('active_id'))
        if reservation_id:
            reservation_id.split(self.nights)
        return True
