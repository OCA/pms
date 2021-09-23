# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ChannelWubookPmsAvailabilityPlanRuleMapperImport(Component):
    _name = "channel.wubook.pms.availability.plan.rule.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.availability.plan.rule"

    direct = [
        ("date", "date"),
        ("no_ota", "no_ota"),
        ("avail", "quota"),
        ("min_stay", "min_stay"),
        ("max_stay", "max_stay"),
        ("min_stay_arrival", "min_stay_arrival"),
        # ("max_stay_arrival", "max_stay_arrival"),
        ("closed", "closed"),
        ("closed_departure", "closed_departure"),
        ("closed_arrival", "closed_arrival"),
    ]

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def property_ids(self, record):
        return {"pms_property_id": self.backend_record.pms_property_id.id}

    @mapping
    def room(self, record):
        rt_binder = self.binder_for("channel.wubook.pms.room.type")
        room_type = rt_binder.to_internal(record["id_room"], unwrap=True)
        if not room_type:
            raise ValidationError(
                _(
                    "External record with id %i not exists. "
                    "It should be imported in _import_dependencies"
                )
                % record["rid"]
            )
        return {
            "room_type_id": room_type.id,
        }
