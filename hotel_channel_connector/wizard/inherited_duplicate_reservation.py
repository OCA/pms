# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo import models, api, _


class MassiveChangesWizard(models.TransientModel):
    _inherit = 'hotel.wizard.duplicate.reservation'

    @api.multi
    def duplicate_reservation(self):
        reservation_id = self.env['hotel.reservation'].browse(
            self.env.context.get('active_id'))
        if reservation_id and reservation_id.is_from_ota:
            raise ValidationError(_("Can't duplicate a reservation from channel"))
        return super(MassiveChangesWizard, self).duplicate_reservation()
