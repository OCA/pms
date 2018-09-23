# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

class ChannelHotelRoomTypeRestrictionItem(models.Model):
    _name = 'channel.hotel.room.type.restriction.item'
    _inherit = 'channel.binding'
    _inherits = {'hotel.room.type.restriction.item': 'odoo_id'}
    _description = 'Channel Hotel Room Type Restriction Item'

    odoo_id = fields.Many2one(comodel_name='hotel.room.type.restriction.item',
                              string='Hotel Virtual Room Restriction',
                              required=True,
                              ondelete='cascade')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @job(default_channel='root.channel')
    @api.multi
    def update_channel_pushed(self, status):
        self.ensure_one()
        self.channel_pushed = status

class HotelRoomTypeRestrictionItem(models.Model):
    _inherit = 'hotel.room.type.restriction.item'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.room.type.restriction.item',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

class ChannelBindingHotelRoomTypeRestrictionItemListener(Component):
    _name = 'channel.binding.hotel.room.type.restriction.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.room.type.restriction']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.update_channel_pushed(False)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.update_channel_pushed(False)
