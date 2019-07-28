# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
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

    @api.model
    def _default_max_avail(self):
        return self.env['hotel.room.type'].browse(
            self._context.get('default_odoo_id')
        ).total_rooms_count or -1

    @api.model
    def _default_availability(self):
        return max(min(self.default_quota, self.default_max_avail), 0)

    odoo_id = fields.Many2one(comodel_name='hotel.room.type',
                              string='Room Type',
                              required=True,
                              ondelete='cascade')
    channel_short_code = fields.Char("Channel Short Code")
    ota_capacity = fields.Integer("OTA's Capacity", default=1,
                                  help="The capacity of the room for OTAs.")

    default_quota = fields.Integer("Default Quota",
                                   help="Quota assigned to the channel given no availability rules. "
                                        "Use `-1` for managing no quota.")
    default_max_avail = fields.Integer("Max. Availability", default=_default_max_avail,
                                       help="Maximum simultaneous availability given no availability rules. "
                                            "Use `-1` for using maximum simultaneous availability.")
    default_availability = fields.Integer(default=_default_availability, readonly=True,
                                          help="Default availability for OTAs. "
                                               "The availability is calculated based on the quota, "
                                               "the maximum simultaneous availability and "
                                               "the total room count for the given room type.")

    min_price = fields.Float('Min. Price', default=5.0, digits=dp.get_precision('Product Price'),
                             help="Setup the min price to prevent incidents while editing your prices.")
    max_price = fields.Float('Max. Price', default=200.0, digits=dp.get_precision('Product Price'),
                             help="Setup the max price to prevent incidents while editing your prices.")

    @api.constrains('default_quota', 'default_max_avail', 'total_rooms_count')
    def _constrains_availability(self):
        for rec in self:
            to_eval = []
            to_eval.append(rec.total_rooms_count)
            if rec.default_quota >= 0:
                to_eval.append(rec.default_quota)
            if rec.default_max_avail >= 0:
                to_eval.append(rec.default_max_avail)

            rec.default_availability = min(to_eval)

    @api.constrains('room_ids')
    def _constrain_capacity(self):
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
            if record.ota_capacity > record.capacity:
                raise ValidationError(_("OTA's capacity can't be greater than room type capacity"))


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

    capacity = fields.Integer("Capacity", compute="_compute_capacity", store=True)

    @api.depends('room_ids')
    def _compute_capacity(self):
        for record in self:
            record.capacity = record.get_capacity()

    @api.constrains('active')
    def _check_active(self):
        for record in self:
            if not record.active and record.total_rooms_count > 0:
                raise ValidationError(
                    _("You can not archive a room type with active rooms.") + " " +
                    _("Please, change the %s room(s) to other room type.") % str(record.total_rooms_count))

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
            action['context'] = {
                'default_odoo_id': self.id,
                'default_name': self.name,
                'default_ota_capacity': self.capacity,
                'default_capacity': self.capacity,
                'default_list_price': self.list_price,
                'default_total_rooms_count': self.total_rooms_count}
        return action

    @api.multi
    def disconnect_channel_bind_ids(self):
        # TODO: multichannel rooms is not implemented
        self.channel_bind_ids.with_context({'connector_no_export': True}).unlink()

    @api.multi
    def write(self, vals):
        if 'active' in vals and vals.get('active') is False:
            self.channel_bind_ids.unlink()
        return super().write(vals)


class BindingHotelRoomTypeListener(Component):
    _name = 'binding.hotel.room.type.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.room.type']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('name', 'list_price', 'total_rooms_count', 'board_service_room_type_ids')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            for binding in record.channel_bind_ids:
                binding.modify_room()


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
