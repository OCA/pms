# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelMapperExport(AbstractComponent):
    _name = "channel.mapper.export"
    _inherit = ["base.export.mapper"]


class ChannelChildMapperExport(AbstractComponent):
    _name = "channel.child.mapper.export"
    _inherit = "base.map.child.export"
