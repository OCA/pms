# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookPmsBoardServiceMapperExport(Component):
    _name = "channel.wubook.pms.board.service.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.pms.board.service"

    direct = [
        ("name", "name"),
        ("default_code", "shortname"),
    ]
