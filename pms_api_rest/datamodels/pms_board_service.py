from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsBoardServiceSearchParam(Datamodel):
    _name = "pms.board.service.search.param"
    name = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)


class PmsBoardServiceInfo(Datamodel):
    _name = "pms.board.service.info"
    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    roomTypeId = fields.Integer(required=True, allow_none=False)
    amount = fields.Float(required=False, allow_none=False)
