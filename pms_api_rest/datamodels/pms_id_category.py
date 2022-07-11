from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsIdCategoryInfo(Datamodel):
    _name = "pms.id.category.info"
    id = fields.Integer(required=False, allow_none=True)
    documentType = fields.String(required=False, allow_none=True)
