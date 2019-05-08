# Copyright 2017  Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT)


class ServiceOnDay(models.TransientModel):
    _name = 'service.on.day'

    def _get_default_date(self):
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        today = fields.Date.context_today(self.with_context(tz=tz_hotel))
        return fields.Date.from_string(today).strftime(DEFAULT_SERVER_DATE_FORMAT)


    product_id = fields.Many2one('product.product', 'Service', required=True,
                                 domain=[('per_day', '=', True)])
    product_qty = fields.Integer('Quantity', default=1)
    date = fields.Date('Date', default=_get_default_date)

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
