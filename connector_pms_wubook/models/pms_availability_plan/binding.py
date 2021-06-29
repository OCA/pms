# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ChannelWubookPmsAvailabilityPlanBinding(models.Model):
    _name = "channel.wubook.pms.availability.plan"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.availability.plan": "odoo_id"}

    # binding fields
    odoo_id = fields.Many2one(
        comodel_name="pms.availability.plan",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    channel_wubook_rule_ids = fields.One2many(
        string="Wubook Availability Rules",
        help="Rules in a availability plan",
        comodel_name="channel.wubook.pms.availability.plan.rule",
        inverse_name="channel_wubook_availability_plan_id",
    )

    @api.model
    def import_data(
        self,
        backend_id,
        date_from,
        date_to,
        room_type_ids,
        delayed=False,
    ):
        """ Prepare the batch import of Availability Plans from Channel """
        domain = []
        if date_from and date_to:
            domain += [
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ]
        # TODO: duplicated code, unify
        if room_type_ids:
            with backend_id.work_on("channel.wubook.pms.room.type") as work:
                binder = work.component(usage="binder")
            external_ids = []
            for rt in room_type_ids:
                binding = binder.wrap_record(rt)
                if not binding or not binding.external_id:
                    raise NotImplementedError(
                        _(
                            "The Room type %s has no binding. Import of Odoo records "
                            "without binding is not supported yet"
                        )
                        % rt.name
                    )
                external_ids.append(binding.external_id)
            domain.append(("id_room", "in", external_ids))
        return self.import_batch(
            backend_record=backend_id, domain=domain, delayed=delayed
        )

    @api.model
    def export_data(self, backend_record=None):
        """ Prepare the batch export of Availability Plan to Channel """
        return self.export_batch(
            backend_record=backend_record,
            domain=[
                # ("name", "=", "wete"),
                "|",
                ("pms_property_ids", "=", False),
                ("pms_property_ids", "in", backend_record.pms_property_id.ids),
            ],
        )

    def resync_import(self):
        for record in self:
            items = record.rule_ids.filtered(
                lambda x: x.pms_property_id == self.backend_id.pms_property_id
            )
            if items:
                date_from = min(items.mapped("date"))
                date_to = max(items.mapped("date"))
                room_types = items.mapped("room_type_id")
                record.import_data(
                    self.backend_id,
                    date_from,
                    date_to,
                    room_types,
                    delayed=False,
                )
