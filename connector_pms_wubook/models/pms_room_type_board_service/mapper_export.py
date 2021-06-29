# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ChannelWubookPmsRoomTypeBoardServiceMapperExport(Component):
    _name = "channel.wubook.pms.room.type.board.service.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.pms.room.type.board.service"

    @mapping
    def boards(self, record):
        board_service = record.pms_board_service_id
        bs_binder = self.binder_for("channel.wubook.pms.board.service")
        external_id = bs_binder.to_external(board_service, wrap=True)
        if not external_id:
            raise ValidationError(
                _(
                    "External record of Board Service [%s] %s does not exists. "
                    "It should be exported in _export_dependencies"
                )
                % (board_service.default_code, board_service.name)
            )
        return {
            external_id: {
                "dtype": 2,
                "value": record.amount * record.pms_room_type_id.get_capacity(),
            }
        }
