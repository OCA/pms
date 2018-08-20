# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

class ChannelHotelRoomType(models.Model):
    _name = 'channel.hotel.room.type'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type': 'odoo_id'}
    _description = 'Channel Hotel Room'

    @api.depends('ota_capacity')
    @api.onchange('room_ids', 'room_type_ids')
    def _get_capacity(self):
        for rec in self:
            rec.ota_capacity = rec.get_capacity()

    odoo_id = fields.Many2one(comodel_names='hotel.room.type',
                              string='Room Type',
                              required=True,
                              ondelete='cascade')
    channel_room_id = fields.Char("Channel Room ID", readonly=True, old_name='wrid')
    channel_short_code = fields.Char("Channel Short Code", readonly=True, old_name='wscode')
    ota_capacity = fields.Integer("OTA's Capacity", default=1, old_name='wcapacity')

    @api.constrains('ota_capacity')
    def _check_ota_capacity(self):
        for record in self:
            if record.ota_capacity < 1:
                raise ValidationError(_("OTA's capacity can't be less than one"))

    @api.multi
    @api.constrains('channel_short_code')
    def _check_channel_short_code(self):
        for record in self:
            if len(record.channel_short_code) > 4:  # Wubook scode max. length
                raise ValidationError(_("Chanel short code can't be longer than 4 characters"))

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def create_room(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            seq_obj = self.env['ir.sequence']
            shortcode = seq_obj.next_by_code('hotel.room.type')[:4]
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    channel_room_id = adapter.create_room(
                        shortcode,
                        self.name,
                        self.ota_capacity,
                        self.list_price,
                        self.max_real_rooms)
                    if channel_room_id:
                        self.write({
                            'channel_room_id': channel_room_id,
                            'channel_short_code': shortcode,
                        })
                except ValidationError as e:
                    self.create_issue('room', "Can't create room on channel", "sss")

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def modify_room(self):
        self.ensure_one()
        if self._context.get('channel_action', True) and self.channel_room_id:
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    adapter.modify_room(
                        self.channel_room_id,
                        self.name,
                        self.ota_capacity,
                        self.list_price,
                        self.max_real_rooms,
                        self.channel_short_code)
                except ValidationError as e:
                    self.create_issue('room', "Can't modify room on channel", "sss")

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def delete_room(self):
        self.ensure_one()
        if self._context.get('channel_action', True) and self.channel_room_id:
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    adapter.delete_room(self.channel_room_id)
                except ValidationError as e:
                    self.create_issue('room', "Can't delete room on channel", "sss")

    @job(default_channel='root.channel')
    @api.multi
    def import_rooms(self):
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                importer = work.component(usage='channel.importer')
                return importer.import_rooms()

class HotelRoomType(models.Model):
    _inherit = 'hotel.room.type'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')


    @api.multi
    def get_restrictions(self, date):
        restriction_plan_id = int(self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_restrictions_id'))
        self.ensure_one()
        restriction = self.env['hotel.virtual.room.restriction.item'].search([
            ('date_start', '=', date),
            ('date_end', '=', date),
            ('virtual_room_id', '=', self.id),
            ('restriction_id', '=', restriction_plan_id)
        ], limit=1)
        return restriction

class ChannelBindingRoomTypeListener(Component):
    _name = 'channel.binding.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.with_delay(priority=20).create_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.with_delay(priority=20).delete_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.with_delay(priority=20).modidy_room()
