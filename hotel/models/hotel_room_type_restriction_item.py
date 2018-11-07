# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelRoomTypeRestrictionItem(models.Model):
    _name = 'hotel.room.type.restriction.item'

    restriction_id = fields.Many2one('hotel.room.type.restriction',
                                     'Restriction Plan', ondelete='cascade',
                                     index=True)
    room_type_id = fields.Many2one('hotel.room.type', 'Room Type',
                                   required=True, ondelete='cascade')
    date = fields.Date('Date')
    applied_on = fields.Selection([
        ('1_global', 'Global'),
        ('0_room_type', 'Room Type')], string="Apply On", required=True,
                                  default='0_room_type',
                                  help='Pricelist Item applicable on selected option')

    min_stay = fields.Integer("Min. Stay")
    min_stay_arrival = fields.Integer("Min. Stay Arrival")
    max_stay = fields.Integer("Max. Stay")
    max_stay_arrival = fields.Integer("Max. Stay Arrival")
    closed = fields.Boolean('Closed')
    closed_departure = fields.Boolean('Closed Departure')
    closed_arrival = fields.Boolean('Closed Arrival')

    _sql_constraints = [('room_type_registry_unique',
                         'unique(restriction_id, room_type_id, date)',
                         'Only can exists one restriction in the same day for the same room type!')]

    @api.multi
    @api.constrains('min_stay', 'min_stay_arrival', 'max_stay',
                    'max_stay_arrival')
    def _check_min_stay(self):
        for record in self:
            if record.self.min_stay < 0:
                raise ValidationError(_("Min. Stay can't be less than zero"))
            elif record.min_stay_arrival < 0:
                raise ValidationError(
                    ("Min. Stay Arrival can't be less than zero"))
            elif record.max_stay < 0:
                raise ValidationError(_("Max. Stay can't be less than zero"))
            elif record.max_stay_arrival < 0:
                raise ValidationError(
                    ("Max. Stay Arrival can't be less than zero"))

    @api.constrains('applied_on')
    def _check_applied_on(self):
        for record in self:
            count = record.search_count([('applied_on', '=', '1_global')])
            if count > 1:
                raise ValidationError(_("Already exists an global rule"))
