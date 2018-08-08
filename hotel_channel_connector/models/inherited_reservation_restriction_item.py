# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class ReservationRestrictionItem(models.Model):
    _inherit = 'hotel.virtual.room.restriction.item'

    wpushed = fields.Boolean("WuBook Pushed", default=False, readonly=True)

    @api.onchange('date_start')
    def _onchange_date_start(self):
        self.date_end = self.date_start

    @api.model
    def create(self, vals):
        if vals.get('date_start'):
            vals['date_end'] = vals.get('date_start')
        return super(ReservationRestrictionItem, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('date_start'):
            vals['date_end'] = vals.get('date_start')
        if self._context.get('wubook_action', True):
            vals.update({'wpushed': False})
        return super(ReservationRestrictionItem, self).write(vals)
