# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChannelWubookPmsPropertyAvailabilityBinding(models.Model):
    _name = "channel.wubook.pms.property.availability"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.property": "odoo_id"}

    external_id = fields.Char(string="External ID")

    odoo_id = fields.Many2one(
        comodel_name="pms.property",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    channel_wubook_availability_ids = fields.One2many(
        string="Wubook Availability",
        help="Property availability",
        comodel_name="channel.wubook.pms.availability",
        inverse_name="channel_wubook_property_availability_id",
    )

    # @api.model
    # def import_data(
    #     self,
    #     backend_id,
    #     date_from,
    #     date_to,
    #     room_type_ids=None,
    #     plan_ids=None,
    #     delayed=True,
    # ):
    #     """ Prepare the batch import of Availability Plans from Channel """
    #     domain = []
    #     if date_from and date_to:
    #         domain += [
    #             ("date", ">=", date_from),
    #             ("date", "<=", date_to),
    #         ]
    #     # TODO: duplicated code, unify
    #     if room_type_ids:
    #         with backend_id.work_on("channel.wubook.pms.room.type") as work:
    #             binder = work.component(usage="binder")
    #         external_ids = []
    #         for rt in room_type_ids:
    #             binding = binder.wrap_record(rt)
    #             if not binding or not binding.external_id:
    #                 raise NotImplementedError(
    #                     _(
    #                         "The Room type %s has no binding. Import of Odoo records "
    #                         "without binding is not supported yet"
    #                     )
    #                     % rt.name
    #                 )
    #             external_ids.append(binding.external_id)
    #         domain.append(("id_room", "in", external_ids))
    #     if plan_ids:
    #         with backend_id.work_on("channel.wubook.pms.property.availability") as work:
    #             binder = work.component(usage="binder")
    #         external_ids = []
    #         for plan in plan_ids:
    #             binding = binder.wrap_record(plan)
    #             if not binding or not binding.external_id:
    #                 raise NotImplementedError(
    #                     _(
    #                         "The Availability Plan %s has no binding. Import of Odoo records "
    #                         "without binding is not supported yet"
    #                     )
    #                     % plan.name
    #                 )
    #             external_ids.append(binding.external_id)
    #         domain.append(("id", "in", external_ids))
    #     return self.import_batch(
    #         backend_record=backend_id, domain=domain, delayed=delayed
    #     )
    #
    # @api.model
    # def export_data(self, backend_record=None):
    #     """ Prepare the batch export of Availability Plan to Channel """
    #     return self.export_batch(
    #         backend_record=backend_record,
    #         domain=[
    #             # ("name", "=", "wete"),
    #             "|",
    #             ("pms_property_ids", "=", False),
    #             ("pms_property_ids", "in", backend_record.pms_property_id.ids),
    #         ],
    #     )
    #
    # def resync_import(self):
    #     for record in self:
    #         if record.availability_ids:
    #             date_from = min(items.mapped("date"))
    #             date_to = max(items.mapped("date"))
    #             room_types = items.mapped("room_type_id")
    #             record.import_data(
    #                 self.backend_id,
    #                 date_from,
    #                 date_to,
    #                 room_type_ids=room_types,
    #                 plan_ids=record.odoo_id,
    #                 delayed=False,
    #             )