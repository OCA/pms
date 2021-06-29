# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ChannelWubookPmsRoomTypeBoardServiceMapperImport(Component):
    _name = "channel.wubook.pms.room.type.board.service.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.room.type.board.service"

    @only_create
    @mapping
    def boards(self, record):
        bd_binder = self.binder_for("channel.wubook.pms.board.service")
        board_service = bd_binder.to_internal(record["id"], unwrap=True)
        assert board_service, (
            "board_service_id %s should have been imported in "
            "PmsRoomTypeImporter._import_dependencies" % (record["id"],)
        )
        return {
            "by_default": record["default"] != 0,
            "pms_board_service_id": board_service.id,
        }
        # TODO heuristic to import board service price
