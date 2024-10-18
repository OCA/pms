# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component


class ChannelWubookPmsRoomTypeClassBinder(Component):
    _name = "channel.wubook.pms.room.type.class.binder"
    _inherit = "channel.wubook.binder"

    _apply_on = "channel.wubook.pms.room.type.class"

    _internal_alt_id = ("default_code", "pms_property_ids")
    _external_alt_id = "shortname"

    def _get_internal_record_alt(self, model_name, values):
        pms_property_id = values["pms_property_ids"][0][1]
        records = self.env[model_name].search(
            [
                "&",
                ("default_code", "=", values["default_code"]),
                "|",
                ("pms_property_ids", "in", pms_property_id),
                ("pms_property_ids", "=", False),
            ]
        )

        res, res_priority = self.env[model_name], -1
        for rec in records:
            priority = (
                rec.pms_property_ids
                and pms_property_id in rec.pms_property_ids.ids
                and 1
            ) or 0
            if priority > res_priority:
                res, res_priority = rec, priority
            elif priority == res_priority:
                raise ValidationError(
                    _(
                        "Integrity error: There's more than one room type "
                        "with same code and properties"
                    )
                )

        return res

    # TODO: almost identical code as on room type and board services -> Unify
