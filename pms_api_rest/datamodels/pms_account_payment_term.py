from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAccountPaymentTermInfo(Datamodel):
    _name = "pms.account.payment.term.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
