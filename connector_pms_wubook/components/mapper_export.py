# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelMapperExport(AbstractComponent):
    _name = "channel.wubook.mapper.export"
    _inherit = ["channel.mapper.export", "base.channel.wubook.connector"]


class ChannelWubookChildMapperExport(AbstractComponent):
    _name = "channel.wubook.child.mapper.export"
    _inherit = ["channel.child.mapper.export", "base.channel.wubook.connector"]


class ChannelWubookChildBinderMapperExport(AbstractComponent):
    _name = "channel.wubook.child.binder.mapper.export"
    _inherit = ["channel.child.binder.mapper.export", "base.channel.wubook.connector"]
