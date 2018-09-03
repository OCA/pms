# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
import logging
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class HotelService(models.Model):

    @api.model
    def _service_checkin(self):
        if 'checkin' in self._context:
            return self._context['checkin']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _service_checkout(self):
        if 'checkout' in self._context:
            return self._context['checkout']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _default_ser_room_line(self):
        if 'room_lines' in self.env.context and self.env.context['room_lines']:
            ids = [item[1] for item in self.env.context['room_lines']]
            return self.env['hotel.reservation'].search([
                ('id', 'in', ids),
            ], limit=1)
        return False

    _name = 'hotel.service'
    _description = 'Hotel Services and its charges'

    name = fields.Char('Service description')
    # services in the hotel are products
    product_id = fields.Many2one('product.product', 'Service', required=True)

    folio_id = fields.Many2one('hotel.folio', 'Folio', ondelete='cascade')

    ser_room_line = fields.Many2one('hotel.reservation', 'Room',
                                    default=_default_ser_room_line)

    list_price = fields.Float(
        related='product_id.list_price')

    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web')], 'Sales Channel')

    ser_checkin = fields.Datetime('From Date', required=True,
                                  default=_service_checkin)
    ser_checkout = fields.Datetime('To Date', required=True,
                                   default=_service_checkout)


    # TODO Hierarchical relationship for parent-child tree
    # parent_id = fields.Many2one ...

    # service_id = fields.Many2one('product.product', 'Service_id',
    #                              required=True, ondelete='cascade',
    #                              delegate=True)
    # service_type_id = fields.Many2one('hotel.service.type',
                                      # 'Service Catagory')
    # service_line_id = fields.Many2one('hotel.service.line',
    #                                   'Service Line')
    # @api.multi
    # def unlink(self):
    #     # for record in self:
    #         # record.service_id.unlink()
    #     return super(HotelServices, self).unlink()
