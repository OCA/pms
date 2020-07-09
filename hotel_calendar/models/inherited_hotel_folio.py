# Copyright 2018-2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, _


class HotelFolio(models.Model):
    _inherit = 'hotel.folio'

    # ORM overrides
    
    def write(self, vals):
        ret = super(HotelFolio, self).write(vals)
        fields_to_check = ('reservation_ids', 'service_ids', 'pending_amount')
        fields_checked = [elm for elm in fields_to_check if elm in vals]
        if any(fields_checked):
            for record in self:
                record.reservation_ids.send_bus_notification('write', 'noshow')
        return ret

    
    def unlink(self):
        for record in self:
            record.reservation_ids.send_bus_notification('unlink', 'warn',
                                                    _("Folio Deleted"))
        return super(HotelFolio, self).unlink()

    # Business methods
    
    def compute_amount(self):
        ret = super(HotelFolio, self).compute_amount()
        with self.env.norecompute():
            for record in self:
                record.reservation_ids.send_bus_notification('write', 'noshow')
        return ret
