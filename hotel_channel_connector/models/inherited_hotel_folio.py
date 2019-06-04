# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons.queue_job.job import job


class HotelFolio(models.Model):
    _inherit = 'hotel.folio'

    @api.depends('room_lines')
    def _has_channel_reservations(self):
        for record in self:
            channel_reservations = record.room_lines.filtered(lambda x: x.room_id)
            record.has_channel_reservations = any(channel_reservations)

    customer_notes = fields.Text("Channel Customer Notes",
                                 readonly=True, old_name='wcustomer_notes')
    has_channel_reservations = fields.Boolean(compute=_has_channel_reservations,
                                              store=False,
                                              old_name='whas_wubook_reservations')
    unconfirmed_channel_price = fields.Boolean(default=False)

    @job(default_channel='root.channel')
    @api.model
    def import_reservations(self):
        with self.backend_id.work_on(self._name) as work:
            importer = work.component(usage='channel.importer')
            importer.fetch_new_bookings()

    @api.multi
    def action_confirm(self):
        for rec in self:
            rec.room_lines.write({
                'to_assign': False,
            })
        return super().action_confirm()

    @api.multi
    def get_grouped_reservations_json(self, state, import_all=False):
        super().get_grouped_reservations_json(state, import_all=import_all)
        self.ensure_one()
        info_grouped = []
        for rline in self.room_lines:
            if (import_all or rline.to_send) and not rline.parent_reservation and rline.state == state and ((rline.state == 'cancelled' and not rline.channel_modified) or rline.state != 'cancelled'):
                dates = (rline.real_checkin, rline.real_checkout)
                vals = {
                    'num': len(
                        self.room_lines.filtered(lambda r: r.real_checkin == dates[0] and r.real_checkout == dates[1] and r.room_type_id.id == rline.room_type_id.id and (r.to_send or import_all) and not r.parent_reservation and r.state == rline.state and ((r.state == 'cancelled' and not r.channel_modified) or r.state != 'cancelled'))
                    ),
                    'room_type': {
                        'id': rline.room_type_id.id,
                        'name': rline.room_type_id.name,
                    },
                    'checkin': dates[0],
                    'checkout': dates[1],
                    'nights': len(rline.reservation_line_ids),
                    'adults': rline.adults,
                    'childrens': rline.children,
                }
                founded = False
                for srline in info_grouped:
                    if srline['num'] == vals['num'] and srline['room_type']['id'] == vals['room_type']['id'] and srline['checkin'] == vals['checkin'] and srline['checkout'] == vals['checkout']:
                        founded = True
                        break
                if not founded:
                    info_grouped.append(vals)
        return sorted(sorted(info_grouped, key=lambda k: k['num'],
                             reverse=True), key=lambda k: k['room_type']['id'])

    @api.depends('room_lines')
    def _compute_has_cancelled_reservations_to_send(self):
        super()._compute_has_cancelled_reservations_to_send()
        channel_hotel_reserv_obj = self.env['channel.hotel.reservation']
        for record in self:
            splitted_reservation_ids = record.room_lines.filtered(lambda x: x.splitted)
            has_to_send = False
            for rline in splitted_reservation_ids:
                master_reservation = rline.parent_reservation or rline
                has_to_send = channel_hotel_reserv_obj.search_count([
                    ('splitted', '=', True),
                    ('folio_id', '=', self.id),
                    ('to_send', '=', True),
                    ('state', '=', 'cancelled'),
                    ('channel_modified', '=', False),
                    '|',
                    ('parent_reservation', '=', master_reservation.id),
                    ('id', '=', master_reservation.id),
                ]) > 0
                if has_to_send:
                    break
            record.has_cancelled_reservations_to_send = has_to_send
