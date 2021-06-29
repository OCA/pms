# Copyright NuoBiT Solutions, S.L. (<https://www.nuobit.com>)
# Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class ChannelWubookPmsAvailabilityListener(Component):
    _name = "channel.wubook.pms.availability.listener"
    _inherit = "channel.wubook.listener"

    _apply_on = "channel.wubook.pms.availability"

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        for backend_id in record.room_type_id.channel_wubook_bind_ids.backend_id:
            self.env["channel.wubook.pms.availability"].export_record(
                backend_id, record
            )
