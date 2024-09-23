from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsSaleChannelSearchParam(Datamodel):
    _name = "pms.sale.channel.search.param"
    pmsPropertyIds = fields.List(fields.Integer(), required=False)


class PmsSaleChannelInfo(Datamodel):
    _name = "pms.sale.channel.info"
    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    channelType = fields.String(required=True, allow_none=True)
    iconUrl = fields.String(required=False, allow_none=True)
