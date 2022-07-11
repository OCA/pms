from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsBoardServiceLineSearchParam(Datamodel):
    _name = "pms.board.service.line.search.param"
    boardServiceId = fields.Integer(required=True, allow_none=False)


class PmsBoardServiceLineInfo(Datamodel):
    _name = "pms.board.service.line.info"
    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    boardServiceId = fields.Integer(required=True, allow_none=False)
    productId = fields.Integer(required=True, allow_none=False)
    amount = fields.Float(required=False, allow_none=False)
