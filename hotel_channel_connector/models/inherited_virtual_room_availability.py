# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.hotel import date_utils
from ..wubook import DEFAULT_WUBOOK_DATE_FORMAT


class VirtualRoomAvailability(models.Model):
    _inherit = 'hotel.virtual.room.availability'

    @api.model
    def _default_channel_max_avail(self):
        if self.virtual_room_id:
            return self.virtual_room_id.max_real_rooms
        return -1

    channel_max_avail = fields.Integer("Max. Channel Avail",
                                       default=_default_channel_max_avail,
                                       old_name='wmax_avail')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @api.constrains('avail')
    def _check_avail(self):
        vroom_obj = self.env['hotel.virtual.room']
        issue_obj = self.env['hotel.channel.connector.issue']
        wubook_obj = self.env['wubook']
        for record in self:
            cavail = len(vroom_obj.check_availability_virtual_room(
                record.date,
                record.date,
                virtual_room_id=record.virtual_room_id.id))
            max_avail = min(cavail, record.virtual_room_id.total_rooms_count)
            if record.avail > max_avail:
                issue_obj.sudo().create({
                    'section': 'avail',
                    'message': _(r"The new availability can't be greater than \
                        the actual availability \
                        \n[%s]\nInput: %d\Limit: %d") % (record.virtual_room_id.name,
                                                         record.avail,
                                                         record),
                    'wid': record.virtual_room_id.wrid,
                    'date_start': record.date,
                    'date_end': record.date,
                })
                # Auto-Fix wubook availability
                date_dt = date_utils.get_datetime(record.date)
                wubook_obj.update_availability([{
                    'id': record.virtual_room_id.wrid,
                    'days': [{
                        'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        'avail': max_avail,
                    }],
                }])
        return super(VirtualRoomAvailability, self)._check_avail()

    @api.constrains('wmax_avail')
    def _check_wmax_avail(self):
        for record in self:
            if record.wmax_avail > record.virtual_room_id.total_rooms_count:
                raise ValidationError(_("max avail for wubook can't be high \
                    than toal rooms \
                    count: %d") % record.virtual_room_id.total_rooms_count)

    @api.onchange('virtual_room_id')
    def onchange_virtual_room_id(self):
        if self.virtual_room_id:
            self.wmax_avail = self.virtual_room_id.max_real_rooms

    @api.multi
    def write(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            vals.update({'wpushed': False})
        return super(VirtualRoomAvailability, self).write(vals)

    @api.model
    def refresh_availability(self, checkin, checkout, product_id):
        date_start = date_utils.get_datetime(checkin)
        # Not count end day of the reservation
        date_diff = date_utils.date_diff(checkin, checkout, hours=False)

        vroom_obj = self.env['hotel.room.type']
        virtual_room_avail_obj = self.env['hotel.virtual.room.availability']

        vrooms = vroom_obj.search([
            ('room_ids.product_id', '=', product_id)
        ])
        for vroom in vrooms:
            if vroom.wrid and vroom.wrid != '':
                for i in range(0, date_diff):
                    ndate_dt = date_start + timedelta(days=i)
                    ndate_str = ndate_dt.strftime(
                                                DEFAULT_SERVER_DATE_FORMAT)
                    avail = len(vroom_obj.check_availability_virtual_room(
                        ndate_str,
                        ndate_str,
                        virtual_room_id=vroom.id))
                    max_avail = vroom.max_real_rooms
                    vroom_avail_id = virtual_room_avail_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', ndate_str)], limit=1)
                    if vroom_avail_id and vroom_avail_id.wmax_avail >= 0:
                        max_avail = vroom_avail_id.wmax_avail
                    avail = max(
                            min(avail, vroom.total_rooms_count, max_avail), 0)

                    if vroom_avail_id:
                        vroom_avail_id.write({'avail': avail})
                    else:
                        virtual_room_avail_obj.create({
                            'virtual_room_id': vroom.id,
                            'date': ndate_str,
                            'avail': avail,
                        })
