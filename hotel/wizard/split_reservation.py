# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta
from openerp.exceptions import ValidationError
from openerp import models, fields, api, _
from openerp.tools import (
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)


class SplitReservationWizard(models.TransientModel):
    _name = 'hotel.wizard.split.reservation'

    nights = fields.Integer('Nights', default=1, min=1)

    @api.multi
    def split_reservation(self):
        reservation_id = self.env['hotel.reservation'].browse(
            self.env.context.get('active_id'))
        if reservation_id:
            date_start_dt = fields.Date.from_string(reservation_id.checkin)
            date_end_dt = fields.Date.from_string(reservation_id.checkout)
            date_diff = abs((date_end_dt - date_start_dt).days)
            for record in self:
                new_start_date_dt = date_start_dt + \
                                    timedelta(days=date_diff-record.nights)
                if record.nights >= date_diff or record.nights < 1:
                    raise ValidationError(_("Invalid Nights! Max is \
                                            '%d'") % (date_diff-1))

                vals = reservation_id.generate_copy_values(
                    new_start_date_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    date_end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                )
                # Days Price
                reservation_lines = [[], []]
                tprice = [0.0, 0.0]
                for rline in reservation_id.reservation_lines:
                    rline_dt = fields.Date.from_string(rline.date)
                    if rline_dt >= new_start_date_dt:
                        reservation_lines[1].append((0, False, {
                            'date': rline.date,
                            'price': rline.price
                        }))
                        tprice[1] += rline.price
                        reservation_lines[0].append((2, rline.id, False))
                    else:
                        tprice[0] += rline.price

                reservation_id.write({
                    'checkout': new_start_date_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'price_unit': tprice[0],
                    'splitted': True,
                })
                reservation_id.reservation_lines = reservation_lines[0]
                parent_res = reservation_id.parent_reservation or \
                    reservation_id
                vals.update({
                    'splitted': True,
                    'price_unit': tprice[1],
                    'parent_reservation': parent_res.id,
                    'room_type_id': parent_res.room_type_id.id,
                    'discount': parent_res.discount,
                })
                reservation_copy = self.env['hotel.reservation'].create(vals)
                if not reservation_copy:
                    raise ValidationError(_("Unexpected error copying record. \
                                            Can't split reservation!"))
                reservation_copy.reservation_lines = reservation_lines[1]
            # return {
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'hotel.folio',
            #     'views': [[False, "form"]],
            #     'target': 'new',
            #     'res_id': reservation_id.folio_id.id,
            # }
        return True
