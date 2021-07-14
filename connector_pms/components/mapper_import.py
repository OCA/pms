# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelMapperImport(AbstractComponent):
    _name = "channel.mapper.import"
    _inherit = "base.import.mapper"


class ChannelChildMapperImport(AbstractComponent):
    _name = "channel.child.mapper.import"
    _inherit = "base.map.child.import"


class ChannelChildBinderMapperImport(AbstractComponent):
    _name = "channel.child.binder.mapper.import"
    _inherit = "base.map.child.binder.import"
