# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class HotelRoomTypeClass(models.Model):
    _inherit = 'hotel.room.type.class'

    _locked_codes = ('1', '2', '3', '4', '5', '6', '7', '8')

    @api.multi
    def write(self, vals):
        for record in self:
            if record.code_class in self._locked_codes:
                raise ValidationError(_("Can't modify channel room type class"))
        return super(HotelRoomTypeClass, self).write(vals)

    @api.multi
    def unlink(self):
        for record in self:
            if record.code_class in self._locked_codes:
                raise ValidationError(_("Can't delete channel room type class"))
        return super(HotelRoomTypeClass, self).unlink()
