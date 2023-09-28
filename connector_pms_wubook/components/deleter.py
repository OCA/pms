# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelWubookDeleter(AbstractComponent):
    _name = "channel.wubook.deleter"
    _inherit = ["channel.deleter", "base.channel.wubook.connector"]
