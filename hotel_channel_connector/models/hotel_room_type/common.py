# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class ChannelHotelRoomType(models.Model):
    _name = 'channel.hotel.room.type'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type': 'odoo_id'}
    _description = 'Channel Hotel Room'

    odoo_id = fields.Many2one(comodel_name='hotel.room.type',
                              string='Room Type',
                              required=True,
                              ondelete='cascade')
    channel_short_code = fields.Char("Channel Short Code", old_name='wscode')
    ota_capacity = fields.Integer("OTA's Capacity", default=1, old_name='wcapacity',
                                  help="The capacity of the room for OTAs.")
    default_availability = fields.Integer(default=0,
                                          help="Default availability for OTAs.")
    min_price = fields.Float('Min. Price', default=5.0, digits=dp.get_precision('Product Price'),
                             help="Setup the min price to prevent incidents while editing your prices.")
    max_price = fields.Float('Max. Price', default=200.0, digits=dp.get_precision('Product Price'),
                             help="Setup the max price to prevent incidents while editing your prices.")

    @api.onchange('room_ids')
    def _get_capacity(self):
        for rec in self:
            rec.ota_capacity = rec.odoo_id.get_capacity()

    def _check_self_unlink(self):
        if not self.odoo_id:
            self.sudo().unlink()

    @job(default_channel='root.channel')
    @api.model
    def import_rooms(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='hotel.room.type.importer')
            return importer.get_rooms()

    @api.constrains('ota_capacity')
    def _check_ota_capacity(self):
        for record in self:
            if record.ota_capacity < 1:
                raise ValidationError(_("OTA's capacity can't be less than one"))

    @api.multi
    @api.constrains('channel_short_code')
    def _check_channel_short_code(self):
        for record in self:
            if self.channel_short_code and len(record.channel_short_code) > 4:  # Wubook scode max. length
                raise ValidationError(_("Chanel short code can't be longer than 4 characters"))

    @job(default_channel='root.channel')
    @api.multi
    def create_room(self):
        self.ensure_one()
        if not self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.exporter')
                exporter.create_room(self)

    @job(default_channel='root.channel')
    @api.multi
    def modify_room(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='hotel.room.type.exporter')
                exporter.modify_room(self)

    @job(default_channel='root.channel')
    @api.multi
    def delete_room(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                deleter = work.component(usage='hotel.room.type.deleter')
                deleter.delete_room(self)

class HotelRoomType(models.Model):
    _inherit = 'hotel.room.type'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

    default_quota = fields.Integer("Default Quota", compute="_compute_capacity")
    capacity = fields.Integer("Capacity", compute="_compute_capacity")

    @api.multi
    def _compute_capacity(self):
        for record in self:
            record.capacity = record.get_capacity()

    @api.onchange('room_ids')
    def _onchange_room_ids(self):
        self._compute_capacity()

    @api.multi
    def get_restrictions(self, date, restriction_plan_id):
        self.ensure_one()
        restriction = self.env['hotel.room.type.restriction.item'].search([
            ('date', '=', date),
            ('room_type_id', '=', self.id),
            ('restriction_id', '=', restriction_plan_id)
        ], limit=1)
        return restriction

    @api.multi
    def open_channel_bind_ids(self):
        channel_bind_ids = self.mapped('channel_bind_ids')
        action = self.env.ref('hotel_channel_connector.channel_hotel_room_type_action').read()[0]
        action['views'] = [(self.env.ref('hotel_channel_connector.channel_hotel_room_type_view_form').id, 'form')]
        action['target'] = 'new'
        if len(channel_bind_ids) == 1:
            action['res_id'] = channel_bind_ids.ids[0]
        elif len(channel_bind_ids) > 1:
            # WARNING: more than one binding is currently not expected
            action['domain'] = [('id', 'in', channel_bind_ids.ids)]
        else:
            action['context'] = {'default_odoo_id': self.id,
                                 'default_name': self.name,
                                 'default_ota_capacity': self.capacity,
                                 'default_list_price': self.list_price}
        return action

    @api.multi
    def sync_from_channel(self):
        channel_bind_ids = self.mapped('channel_bind_ids')
        msg = _("Synchronize room types from the channel manager is not yet implementet.")
        raise UserError(msg)


class BindingHotelRoomTypeListener(Component):
    _name = 'binding.hotel.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('name', 'list_price', 'total_rooms_count')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            for binding in record.channel_bind_ids:
                binding.modify_room()

    # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    # def on_record_create(self, record, fields=None):
    #     record.create_bindings()

class ChannelBindingRoomTypeListener(Component):
    _name = 'channel.binding.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if not record.external_id:
            record.create_room()
        else:
            record.modify_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_room()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        # only fields from channel.hotel.room.type should be listener
        fields_to_check = ('ota_capacity', 'channel_short_code',
                           'min_price', 'max_price', 'default_availability')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.modify_room()
