from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPricelistInfo(Datamodel):
    _name = "pms.pricelist.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(required=False, allow_none=True))
