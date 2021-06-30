# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ChannelWubookPmsAvailabilityMapperExport(Component):
    _name = "channel.wubook.pms.availability.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.pms.availability"

    # direct = [
    #     ("sale_avail", "avail"),
    #     ("date", "date"),
    # ]

    # @changed_by('sale_avail')
    @mapping
    def avail(self, record):
        return {"avail": record.sale_avail}

    # @changed_by('date')
    @mapping
    def date(self, record):
        return {"date": record.date}

    # @changed_by('room_type_id')
    @mapping
    def id_room(self, record):
        room_type = record.room_type_id
        rt_binder = self.binder_for("channel.wubook.pms.room.type")
        external_id = rt_binder.to_external(room_type, wrap=True)
        if not external_id:
            raise ValidationError(
                _(
                    "External record of Room Type id [%s] %s does not exists. "
                    "It should be exported in _export_dependencies"
                )
                % (room_type.default_code, room_type.name)
            )
        return {
            "id_room": external_id,
        }
