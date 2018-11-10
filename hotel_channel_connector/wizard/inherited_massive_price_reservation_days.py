# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo import models, api, _


class MassivePriceChangeWizard(models.TransientModel):
    _inherit = 'hotel.wizard.massive.price.reservation.days'

    @api.multi
    def massive_price_change_days(self):
        self.ensure_one()
        hotel_reservation_obj = self.env['hotel.reservation']
        reservation_id = hotel_reservation_obj.browse(
            self.env.context.get('active_id'))
        if not reservation_id:
            return False

        if reservation_id.is_from_ota:
            raise ValidationError(
                _("Can't change prices of reservations from OTA's"))

        return super(MassivePriceChangeWizard, self).massive_price_change_days()
