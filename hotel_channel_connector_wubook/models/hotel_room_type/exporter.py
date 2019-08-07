# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError


class HotelRoomTypeExporter(Component):
    _inherit = 'channel.hotel.room.type.exporter'

    @api.model
    def modify_room(self, binding):
        try:
            binding.with_context({
                'connector_no_export': True,
            }).write({'sync_date': fields.Datetime.now()})
            # TODO: do not write if backend_adapter.modify_room through an error
            boards = {}
            for board in binding.board_service_room_type_ids:
                if board.channel_service:
                    boards.update(
                        {board.channel_service: {
                            'dtype': 2 if board.price_type == 'fixed' else 1,
                            'value': board.amount * binding.ota_capacity}}
                    ) and board.channel_service
            return self.backend_adapter.modify_room(
                binding.external_id,
                binding.name,
                binding.ota_capacity,
                binding.list_price,
                binding.default_availability,
                binding.channel_short_code,
                'nb',
                {},
                {},
                boards,
                binding.min_price,
                binding.max_price,
                binding.class_id and binding.class_id.code_class or False,
            )
        except ChannelConnectorError as err:
            self.create_issue(
                section='room',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']))

    @api.model
    def create_room(self, binding):
        seq_obj = self.env['ir.sequence']
        short_code = binding.channel_short_code or \
                     seq_obj.next_by_code('hotel.room.type')[:4]
        try:
            boards = {}
            for board in binding.board_service_room_type_ids:
                if board.channel_service:
                    boards.update(
                        {board.channel_service: {
                            'dtype': 2 if board.price_type == 'fixed' else 1,
                            'value': board.amount * binding.ota_capacity}}
                    ) and board.channel_service
            external_id = self.backend_adapter.create_room(
                short_code,
                binding.name,
                binding.ota_capacity,
                binding.list_price,
                binding.default_availability,
                'nb',
                {},
                {},
                boards,
                binding.min_price,
                binding.max_price,
                binding.class_id and binding.class_id.code_class or False,
            )
        except ChannelConnectorError as err:
            self.create_issue(
                section='room',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']))
        else:
            binding.with_context({
                'connector_no_export': True,
            }).write({
                'channel_short_code': short_code,
            })
            self.binder.bind(external_id, binding)
