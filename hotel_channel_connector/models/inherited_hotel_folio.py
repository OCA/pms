# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class HotelFolio(models.Model):
    _inherit = 'hotel.folio'

    @api.depends('room_lines')
    def _has_channel_reservations(self):
        if any(self.room_lines):
            for room in self.room_lines:
                if room.channel_room_id and room.channel_room_id != '':
                    self.has_channel_reservations = True
                    return
        self.has_channel_reservations = False

    seed = fields.Char("WuBook Session Seed", old_name='wseed', readonly=True)
    customer_notes = fields.Text("WuBook Customer Notes",
                                 old_name='wcustomer_notes', readonly=True)
    has_channel_reservations = fields.Boolean(old_name='whas_wubook_reservations',
                                              compute=_has_channel_reservations,
                                              store=False)

    @api.multi
    def import_reservations(self):
        return self.env['hotel.channel.connector'].fetch_new_bookings()

    @api.multi
    def action_confirm(self):
        for rec in self:
            for room in rec.room_lines:
                room.to_read = False
                room.to_assign = False
        return super(HotelFolio, self).action_confirm()

    @api.multi
    def get_grouped_reservations_json(self, state, import_all=False):
        super(HotelFolio, self).get_grouped_reservations_json(state, import_all=import_all)
        self.ensure_one()
        info_grouped = []
        for rline in self.room_lines:
            if (import_all or rline.to_send) and not rline.parent_reservation and rline.state == state and ((rline.state == 'cancelled' and not rline.channel_modified) or rline.state != 'cancelled'):
                dates = rline.get_real_checkin_checkout()
                vals = {
                    'num': len(
                        self.room_lines.filtered(lambda r: r.get_real_checkin_checkout()[0] == dates[0] and r.get_real_checkin_checkout()[1] == dates[1] and r.virtual_room_id.id == rline.virtual_room_id.id and (r.to_send or import_all) and not r.parent_reservation and r.state == rline.state and ((r.state == 'cancelled' and not r.channel_modified) or r.state != 'cancelled'))
                    ),
                    'virtual_room': {
                        'id': rline.virtual_room_id.id,
                        'name': rline.virtual_room_id.name,
                    },
                    'checkin': dates[0],
                    'checkout': dates[1],
                    'nights': len(rline.reservation_line_ids),
                    'adults': rline.adults,
                    'childrens': rline.children,
                }
                founded = False
                for srline in info_grouped:
                    if srline['num'] == vals['num'] and srline['virtual_room']['id'] == vals['virtual_room']['id'] and srline['checkin'] == vals['checkin'] and srline['checkout'] == vals['checkout']:
                        founded = True
                        break
                if not founded:
                    info_grouped.append(vals)
        return sorted(sorted(info_grouped, key=lambda k: k['num'],
                             reverse=True), key=lambda k: k['virtual_room']['id'])

    @api.depends('room_lines')
    def _compute_has_cancelled_reservations_to_send(self):
        super(HotelFolio, self)._compute_has_cancelled_reservations_to_send()
        has_to_send = False
        for rline in self.room_lines:
            if rline.splitted:
                master_reservation = rline.parent_reservation or rline
                has_to_send = self.env['hotel.reservation'].search_count([
                    ('splitted', '=', True),
                    ('folio_id', '=', self.id),
                    ('to_send', '=', True),
                    ('state', '=', 'cancelled'),
                    ('channel_modified', '=', False),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
                    ('id', '=', master_reservation.id),
                ]) > 0
            elif rline.to_send and rline.state == 'cancelled' and not rline.wmodified:
                has_to_send = True
                break
        self.has_cancelled_reservations_to_send = has_to_send
