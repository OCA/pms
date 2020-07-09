# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class PmsReservationLine(models.Model):
    _name = "pms.reservation.line"
    _order = "date"

    # Default Methods ang Gets
    
    def name_get(self):
        result = []
        for res in self:
            date = fields.Date.from_string(res.date)
            name = u'%s/%s' % (date.day, date.month)
            result.append((res.id, name))
        return result

    # Fields declaration
    reservation_id = fields.Many2one(
        'pms.reservation',
        string='Reservation',
        ondelete='cascade',
        required=True,
        copy=False)
    move_line_ids = fields.Many2many(
        'account.move.line',
        'reservation_line_move_rel',
        'reservation_line_id',
        'move_line_id',
        string='Invoice Lines',
        readonly=True,
        copy=False)
    pms_property_id = fields.Many2one(
        'pms.property',
        store=True,
        readonly=True,
        related='reservation_id.pms_property_id')
    date = fields.Date('Date')
    state = fields.Selection(related='reservation_id.state')
    price = fields.Float(
        string='Price',
        digits=dp.get_precision('Product Price'))
    cancel_discount = fields.Float(
        string='Cancel Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)

    # Constraints and onchanges
    @api.constrains('date')
    def constrains_duplicated_date(self):
        for record in self:
            duplicated = record.reservation_id.reservation_line_ids.filtered(
                lambda r: r.date == record.date and
                r.id != record.id
            )
            if duplicated:
                raise ValidationError(_('Duplicated reservation line date'))

    @api.constrains('state')
    def constrains_service_cancel(self):
        for record in self:
            if record.state == 'cancelled':
                room_services = record.reservation_id.service_ids
                for service in room_services:
                    cancel_lines = service.service_line_ids.filtered(
                        lambda r: r.date == record.date
                    )
                    cancel_lines.day_qty = 0
