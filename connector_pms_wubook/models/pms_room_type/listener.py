# Copyright NuoBiT Solutions, S.L. (<https://www.nuobit.com>)
# Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ChannelWubookPmsRoomTypeListener(Component):
    _name = "channel.wubook.pms.room.type.listener"
    _inherit = "channel.wubook.listener"

    _apply_on = "pms.room.type"
