# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ChannelWubookPmsAvailabilityPlanRuleMapperExport(Component):
    _name = "channel.wubook.pms.availability.plan.rule.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.pms.availability.plan.rule"

    direct = [
        ("date", "date"),
        ("min_stay", "min_stay"),
        ("max_stay", "max_stay"),
        ("min_stay_arrival", "min_stay_arrival"),
        ("max_stay_arrival", "max_stay_arrival"),
        ("closed", "closed"),
        ("closed_departure", "closed_departure"),
        # Wubook Bug in 'rplan_update_rplan_values'
        # The field 'closed_arrival' is not exported
        # if in the same call 'closed' = 1.
        # If closed = 0 then 'closed_arrival' is exported correctly
        ("closed_arrival", "closed_arrival"),
        ("no_ota", "no_ota"),
    ]

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
