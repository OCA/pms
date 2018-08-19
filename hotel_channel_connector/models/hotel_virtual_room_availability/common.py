# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action

class ChannelHotelVirtualRoomAvailability(models.Model):
    _name = 'channel.hotel.virtual.room.availability'
    _inherit = 'channel.binding'
    _inherits = {'hotel.virtual.room.availability': 'odoo_id'}
    _description = 'Channel Product Pricelist'

    @api.model
    def _default_channel_max_avail(self):
        if self.virtual_room_id:
            return self.virtual_room_id.max_real_rooms
        return -1

    odoo_id = fields.Many2one(comodel_names='product.pricelist',
                              string='Pricelist',
                              required=True,
                              ondelete='cascade')
    channel_max_avail = fields.Integer("Max. Channel Avail",
                                       default=_default_channel_max_avail,
                                       old_name='wmax_avail')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @api.constrains('channel_max_avail')
    def _check_wmax_avail(self):
        for record in self:
            if record.channel_max_avail > record.virtual_room_id.total_rooms_count:
                raise ValidationError(_("max avail for channel can't be high \
                    than toal rooms \
                    count: %d") % record.virtual_room_id.total_rooms_count)

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def update_availability(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                date_dt = date_utils.get_datetime(self.date)
                adapter.update_availability([{
                    'id': self.virtual_room_id.channel_room_id,
                    'days': [{
                        'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        'avail': self.avail,
                    }],
                }])

class HotelVirtualRoomAvailability(models.Model):
    _inherit = 'hotel.virtual.room.availability'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.virtual.room.availability',
        inverse_name='odoo_id',
        string='Hotel Virtual Room Availability Connector Bindings')

    @api.constrains('avail')
    def _check_avail(self):
        vroom_obj = self.env['hotel.virtual.room']
        issue_obj = self.env['hotel.channel.connector.issue']
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
                self._event('on_fix_channel_availability').notify(record)
        return super(HotelVirtualRoomAvailability, self)._check_avail()

    @api.onchange('virtual_room_id')
    def onchange_virtual_room_id(self):
        if self.virtual_room_id:
            self.channel_max_avail = self.virtual_room_id.max_real_rooms

    @api.multi
    def write(self, vals):
        if self._context.get('channel_action', True):
            vals.update({'channel_pushed': False})
        return super(HotelVirtualRoomAvailability, self).write(vals)

    @api.model
    def refresh_availability(self, checkin, checkout, product_id):
        date_start = date_utils.get_datetime(checkin)
        # Not count end day of the reservation
        date_diff = date_utils.date_diff(checkin, checkout, hours=False)

        vroom_obj = self.env['hotel.virtual.room']
        virtual_room_avail_obj = self.env['hotel.virtual.room.availability']

        vrooms = vroom_obj.search([
            ('room_ids.product_id', '=', product_id)
        ])
        for vroom in vrooms:
            if vroom.channel_room_id:
                for i in range(0, date_diff):
                    ndate_dt = date_start + timedelta(days=i)
                    ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    avail = len(vroom_obj.check_availability_virtual_room(
                        ndate_str,
                        ndate_str,
                        virtual_room_id=vroom.id))
                    max_avail = vroom.max_real_rooms
                    vroom_avail_id = virtual_room_avail_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', ndate_str)], limit=1)
                    if vroom_avail_id and vroom_avail_id.channel_max_avail >= 0:
                        max_avail = vroom_avail_id.channel_max_avail
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

class ChannelBindingHotelVirtualRoomAvailabilityListener(Component):
    _name = 'channel.binding.hotel.virtual.room.availability.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.virtual.room.availability']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_fix_channel_availability(self, record, fields=None):
        record.with_delay(priority=20).update_availability()
