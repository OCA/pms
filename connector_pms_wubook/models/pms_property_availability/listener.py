# Copyright NuoBiT Solutions, S.L. (<https://www.nuobit.com>)
# Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

# class ChannelWubookPmsPropertyAvailabilityListener(Component):
#     _name = "channel.wubook.pms.property.availability.listener"
#     _inherit = "channel.wubook.listener"
#
#     _apply_on = "pms.property.availability"
#
#     def _data(self, record):
#         return f"{record.name}"
#
#     # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     # def on_record_create(self, record, fields=None):
#     #     print("-------------------------- (%s)(%s) LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL model listener create ESPECIFIC %s" % (
#     #         self.env.context.get('saved_from_parent'), record.env.context.get('saved_from_parent'), record._name))
#     #     #super().on_record_create(record, fields=fields)
#     #
#     # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     # def on_record_write(self, record, fields=None):
#     #     print(
#     #         "-------------------------- (%s)(%s) LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL model listener write ESPECIFIC %s"
#     #         % (
#     #             self.env.context.get("saved_from_parent"),
#     #             record.env.context.get("saved_from_parent"),
#     #             record._name
#     #         )
#     #     )
#     #     #super().on_record_write(record, fields=fields)
#
#
# class ChannelWubookPmsPropertyAvailabilityListener(Component):
#     _name = "channel.wubook.pms.property.availability.binding.listener"
#     _inherit = "channel.wubook.binding.listener"
#
#     _apply_on = "channel.wubook.pms.property.availability"
#
#     def _data(self, record):
#         return f"{record.name}"
