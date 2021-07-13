# Copyright NuoBiT Solutions, S.L. (<https://www.nuobit.com>)
# Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import AbstractComponent
from odoo.addons.component_event.components.event import skip_if

class ChannelWubookListener(AbstractComponent):
    _name = "channel.wubook.listener"
    _inherit = "base.connector.listener"

    def _data(self, record):
        return record

    # Create listener on_record_create GENERIC on non-binding model
    # makes no sense because we don't have any bindings yet.
    # We can deal with that on specific models because we know the
    # context exactly like any data that allow us to infer the backend/s
    # where create the binding/s
    # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    # def on_record_create(self, record, fields=None):
    #     print(
    #         "-------------------------- (%s)(%s) LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL model listener create %s"
    #         % (
    #             self.env.context.get("saved_from_parent"),
    #             record.env.context.get("saved_from_parent"),
    #             record,
    #         ),
    #         self._data(record),
    #     )

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        print(
            "-------------------------- (%s)(%s) LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL model listener write %s"
            % (
                self.env.context.get("saved_from_parent"),
                record.env.context.get("saved_from_parent"),
                record,
            ),
            self._data(record),
        )
        for binding in record.channel_wubook_bind_ids:
            binding.export_record(binding.backend_id, record)


# class ChannelWubookBindingListener(AbstractComponent):
#     _name = "channel.wubook.binding.listener"
#     _inherit = "base.connector.listener"
#
#     def _data(self, record):
#         return record
#
#     @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     def on_record_create(self, record, fields=None):
#         print(
#             "-------------------------- (%s)(%s) LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL binding listener create %s"
#             % (
#                 self.env.context.get("saved_from_parent"),
#                 record.env.context.get("saved_from_parent"),
#                 record,
#             ),
#             self._data(record),
#         )
#         record.export_record(record.backend_id, record.odoo_id)
#
#     @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     def on_record_write(self, record, fields=None):
#         print(
#             "-------------------------- (%s)(%s) LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL binding listener write %s"
#             % (
#                 self.env.context.get("saved_from_parent"),
#                 record.env.context.get("saved_from_parent"),
#                 record,
#             ),
#             self._data(record),
#         )
#         record.export_record(record.backend_id, record.odoo_id)
