from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPropertyInfo(Datamodel):
    _inherit = "pms.property.info"
    isUsedRegula = fields.Boolean(required=False, allow_none=True)
