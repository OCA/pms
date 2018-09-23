# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HotelRoomType(models.Model):
    _inherit = 'hotel.room.type'

    hcal_sequence = fields.Integer('Calendar Sequence', default=0)

    @api.multi
    def unlink(self):
        room_type_pr_cached_obj = self.env['room.pricelist.cached']
        for record in self:
            pr_chached = room_type_pr_cached_obj.search([
                ('room_id', '=', record.id)
            ])
            #  Because 'pricelist.cached' is an isolated model,
            # doesn't trigger 'ondelete'. Need call 'unlink' instead.
            pr_chached.unlink()
        return super(HotelRoomType, self).unlink()
