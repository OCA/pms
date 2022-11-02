from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsCashRegisterInfo(Datamodel):
    _name = "pms.cash.register.info"
    id = fields.Integer(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    userId = fields.Integer(required=False, allow_none=True)
    balance = fields.Integer(required=False, allow_none=True)
    dateTime = fields.String(required=False, allow_none=True)


class PmsCashRegisterSearchParam(Datamodel):
    _name = "pms.cash.register.search.param"
    journalId = fields.Integer(required=False, allow_none=True)
