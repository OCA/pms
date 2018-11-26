# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo import fields, models, api


class MassiveChangesWizard(models.TransientModel):
    _inherit = 'hotel.wizard.massive.changes'

    change_no_ota = fields.Boolean(default=False)
    no_ota = fields.Boolean('No OTA', default=False)

    @api.model
    def _get_availability_values(self, ndate, room_type, record):
        vals = super(MassiveChangesWizard, self)._get_availability_values(
            ndate, room_type, record)
        vals.update({
            'channel_max_avail': vals['avail'],
            'no_ota': record.no_ota,
        })
        return vals

    @api.multi
    def massive_change(self):
        res = super(MassiveChangesWizard, self).massive_change()
        self.env['channel.backend'].push_changes()
        return res
