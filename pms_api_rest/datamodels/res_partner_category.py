from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class ResPartnerCategoryInfo(Datamodel):
    _name = "res.partner.category.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    parentId = fields.Integer(required=False, allow_none=True)
