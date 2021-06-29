# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelWubookMapperImport(AbstractComponent):
    _name = "channel.wubook.mapper.import"
    _inherit = ["channel.mapper.import", "base.channel.wubook.connector"]

    # TODO: try to restore this here but solve first the problem
    #   with child mappers which don't need a backend_id
    # @only_create
    # @mapping
    # def backend_id(self, record):
    #     return {"backend_id": self.backend_record.id}


class ChannelWubookChildMapperImport(AbstractComponent):
    _name = "channel.wubook.child.mapper.import"
    _inherit = ["channel.child.mapper.import", "base.channel.wubook.connector"]
