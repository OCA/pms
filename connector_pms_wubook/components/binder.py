# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelWubookBinder(AbstractComponent):
    _name = "channel.wubook.binder"
    _inherit = ["channel.binder", "base.channel.wubook.connector"]

    _bind_ids_field = "channel_wubook_bind_ids"
