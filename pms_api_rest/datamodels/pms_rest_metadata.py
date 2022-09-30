from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRestMetadata(Datamodel):
    _name = "pms.rest.metadata"
    orderBy = fields.String(required=False, allow_none=True)
    limit = fields.Integer(required=False, allow_none=True)
    offset = fields.Integer(required=False, allow_none=True)
