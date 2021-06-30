# Copyright NuoBiT Solutions, S.L. (<https://www.nuobit.com>)
# Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import AbstractComponent
from odoo.addons.component_event import skip_if


class ChannelWubookListener(AbstractComponent):
    _name = "channel.wubook.listener"
    _inherit = "base.connector.listener"

    # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    # def on_record_create(self, record, fields=None):
    #     print("XXXXXXXXXXXX on_record_create", record)
    #     # for binding in record.channel_wubook_bind_ids:
    #     #     binding.resync_export()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for binding in record.channel_wubook_bind_ids:
            binding.resync_export()


class ChannelWubookBindingListener(AbstractComponent):
    _name = "channel.wubook.binding.listener"
    _inherit = "base.connector.listener"

    # @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    # def on_record_create(self, record, fields=None):
    #     print("XXXXXXXXXXXX on_record_create", record)
    #     binding.resync_export()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.resync_export()
