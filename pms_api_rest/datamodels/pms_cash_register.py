from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsCashRegisterInfo(Datamodel):
    _name = "pms.cash.register.info"
    id = fields.Integer(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    userId = fields.Integer(required=False, allow_none=True)
    balance = fields.Float(required=False, allow_none=True)
    dateTime = fields.String(required=False, allow_none=True)


class PmsCashRegisterSearchParam(Datamodel):
    _name = "pms.cash.register.search.param"
    journalId = fields.Integer(required=False, allow_none=True)


class PmsCashRegisterAction(Datamodel):
    _name = "pms.cash.register.action"
    action = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    amount = fields.Float(required=False, allow_none=True)
    journalId = fields.Integer(required=False, allow_none=True)
    forceAction = fields.Boolean(required=False, allow_none=True)


class PmsCashRegisterResult(Datamodel):
    _name = "pms.cash.register.result"
    result = fields.Boolean(required=False, allow_none=False)
    diff = fields.Float(required=False, allow_none=True)
