# Copyright NuoBiT Solutions, S.L. (<https://www.nuobit.com>)
# Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

# from odoo.addons.component.core import Component
# from odoo.addons.component_event.components.event import skip_if
#
# class ChannelWubookPmsAvailabilityPlanRuleListener(Component):
#     _name = "channel.wubook.pms.availability.plan.rule.listener"
#     _inherit = "channel.wubook.listener"
#
#     _apply_on = "pms.availability.plan.rule"
#
#     def _data(self, record):
#         return f"{record.availability_plan_id.name} - {record.room_type_id.name} - {record.date}"
#
#     @skip_if(
#         lambda self, record, **kwargs: self.no_connector_export(record)
#         or record.env.context.get("saved_from_parent")
#     )
#     def on_record_create(self, record, fields=None):
#         backends = record.room_type_id.channel_wubook_bind_ids.backend_id.filtered(
#             lambda x: x.pms_property_id == record.pms_property_id
#         )
#         for backend in backends:
#             record.channel_wubook_bind_ids.export_record(backend, record)
#
#     @skip_if(
#         lambda self, record, **kwargs: self.no_connector_export(record)
#         or record.env.context.get("saved_from_parent")
#     )
#     def on_record_write(self, record, fields=None):
#         super().on_record_write(record, fields=fields)


# class ChannelWubookPmsAvailabilityPlanRuleBindingListener(Component):
#     _name = "channel.wubook.pms.availability.plan.rule.binding.listener"
#     _inherit = "channel.wubook.binding.listener"
#
#     _apply_on = "channel.wubook.pms.availability.plan.rule"
#
#     def _data(self, record):
#         return f"{record.availability_plan_id.name} - {record.room_type_id.name} - {record.date}"
