from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsIdCategoriesInfo(Datamodel):
    _name = "pms.id.categories.info"
    id = fields.Integer(required=False, allow_none=True)
    documentType = fields.String(required=False, allow_none=True)
