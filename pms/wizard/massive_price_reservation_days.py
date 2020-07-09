# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class MassivePriceChangeWizard(models.TransientModel):
    _name = 'pms.wizard.massive.price.reservation.days'
    _description = 'Massive Price Changes'

    new_price = fields.Float('New Price', default=1, min=1)
    change_price = fields.Boolean('Change Prices', default=False)
    new_discount  = fields.Float('New Discount', default=0, min=1)
    change_discount = fields.Boolean('Change Discounts', default=False)


    def massive_price_change_days(self):
        self.ensure_one()
        pms_reservation_obj = self.env['pms.reservation']
        reservation_id = pms_reservation_obj.browse(
            self.env.context.get('active_id'))
        if not reservation_id:
            return False

        cmds = []
        for rline in reservation_id.reservation_line_ids:
            cmds.append((
                1,
                rline.id,
                {
                    'price': self.new_price if self.change_price == True else rline.price,
                    'discount': self.new_discount if self.change_discount == True else rline.discount
                }
            ))
        reservation_id.write({
            'reservation_line_ids': cmds
        })
        return True
