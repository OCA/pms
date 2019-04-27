# Copyright 2017  Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class ServiceOnDay(models.TransientModel):
    _name = 'service.on.day'


    product_id = fields.Many2one('product.product', 'Service', required=True,
                                 domain=[('per_day', '=', True)])
    product_qty = fields.Integer('Quantity', default=1)
    date = fields.Date('Date', default=fields.Date.today())

    @api.multi
    def set_service(self):
        self.ensure_one()
        hotel_reservation_obj = self.env['hotel.reservation']
        reservation = hotel_reservation_obj.browse(
            self.env.context.get('active_id'))
        if not reservation:
            return False
        service_data = [(0, 0, {
            'product_id': self.product_id.id,
            'reservation_id': reservation.id,
            'folio_id': reservation.folio_id.id,
            'product_qty': self.product_qty,
            'service_line_ids': [(0, 0, {
                'date': self.date,
                'day_qty': self.product_qty
                })]
        })]
        reservation.write({
            'service_ids': service_data
        })
        return True
