# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class HotelServiceType(models.Model):
    _name = "hotel.service.type"
    _description = "Service Type"

    name = fields.Char('Service Type', required=True)
    # Used for activate records
    active = fields.Boolean('Active?', default=True)

    # ser_id = fields.Many2one('product.category', 'category', required=True,
    #                          delegate=True, index=True, ondelete='cascade')
    service_ids = fields.One2many('hotel.services', 'service_type_id',
                                  'Services in this category')

    # @api.multi
    # def unlink(self):
    #     # self.ser_id.unlink()
    #     return super(HotelServiceType, self).unlink()
