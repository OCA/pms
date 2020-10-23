# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class BaseChannelConnector(AbstractComponent):
    _name = "base.channel.connector"
    _inherit = "base.connector"

    _description = "Base Channel Connector Component"
