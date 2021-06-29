# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class BaseChannelWubookConnector(AbstractComponent):
    _name = "base.channel.wubook.connector"
    _inherit = "base.channel.connector"

    _collection = "channel.wubook.backend"

    _description = "Base Wubook Channel Connector Component"
