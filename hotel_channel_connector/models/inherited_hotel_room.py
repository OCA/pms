# Copyright 2019 Pablo Q. Barriuso <pabloqb@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    @api.multi
    def write(self, vals):
        """
        Update default availability for segmentation management
        """
        if vals.get('room_type_id'):
            room_type_ids = []
            for record in self:
                room_type_ids.append({
                    'new_room_type_id': vals.get('room_type_id'),
                    'old_room_type_id': record.room_type_id.id,
                })

            res = super().write(vals)

            for item in room_type_ids:
                if item['new_room_type_id']  != item['old_room_type_id']:
                    self.env['channel.hotel.room.type'].search(
                        [('odoo_id', '=', item['old_room_type_id'])]
                    )._onchange_availability()
                    self.env['channel.hotel.room.type'].search(
                        [('odoo_id', '=', item['new_room_type_id'])]
                    )._onchange_availability()
        else:
            res = super().write(vals)
        return res
