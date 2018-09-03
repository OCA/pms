# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class MassivePriceChangeWizard(models.TransientModel):
    _name = 'hotel.wizard.massive.price.reservation.days'

    new_price = fields.Float('New Price', default=1, min=1)

    @api.multi
    def massive_price_change_days(self):
        self.ensure_one()
        hotel_reservation_obj = self.env['hotel.reservation']
        reservation_id = hotel_reservation_obj.browse(
            self.env.context.get('active_id'))
        if not reservation_id:
            return False

        cmds = []
        for rline in reservation_id.reservation_lines:
            cmds.append((
                1,
                rline.id,
                {
                    'price': self.new_price
                }
            ))
        reservation_id.write({
            'reservation_lines': cmds
        })
        # FIXME: For some reason need force reservation price calcs
        reservation_id._computed_amount_reservation()
        # FIXME: Workaround for dispatch updated price
        reservation_id.folio_id.write({
            'room_lines': [
                (
                    1,
                    reservation_id.id, {
                        'reservation_lines': cmds
                    }
                )
            ]
        })

        return True
