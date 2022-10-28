from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsAccountMoveInfo(Datamodel):
    _name = "pms.account.move.info"
    id = fields.Integer(required=False, allow_none=True)
    amount = fields.Float(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    paymentState = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    moveLines = fields.List(NestedModel("pms.invoice.line.info"))
