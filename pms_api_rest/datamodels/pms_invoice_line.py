from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsInvoiceLineInfo(Datamodel):
    _name = "pms.invoice.line.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    quantity = fields.Float(required=False, allow_none=True)
    total = fields.Float(required=False, allow_none=True)
    displayType = fields.String(required=False, allow_none=True)
