from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPricelistItemSearchParam(Datamodel):
    _name = "pms.pricelist.item.search.param"
    date_from = fields.String(required=True, allow_none=False)
    date_to = fields.String(required=True, allow_none=False)
    pms_property_id = fields.Integer(required=True, allow_none=False)
