from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAccountJournalInfo(Datamodel):
    _name = "pms.account.journal.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    allowedPayments = fields.Boolean(required=False, allow_none=True)
