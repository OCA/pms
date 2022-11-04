from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsMailInfo(Datamodel):
    _name = "pms.mail.info"
    subject = fields.String(required=False, allow_none=True)
    bodyMail = fields.String(required=False, allow_none=True)
    partnerIds = fields.List(fields.Integer(), required=False)
    emailAddresses = fields.List(fields.String(), required=False)
