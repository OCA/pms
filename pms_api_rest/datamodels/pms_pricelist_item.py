from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPricelistItemSearchParam(Datamodel):
    _name = "pms.pricelist.item.search.param"
    date_from = fields.String(required=True, allow_none=False)
    date_to = fields.String(required=True, allow_none=False)
    pms_property_id = fields.Integer(required=True, allow_none=False)


class PmsPricelistItemInfo(Datamodel):
    _name = "pms.pricelist.item.info"
    pricelist_item_id = fields.Integer(required=False, allow_none=True)
    availability_rule_id = fields.Integer(required=False, allow_none=True)
    fixed_price = fields.Float(required=False, allow_none=True)
    min_stay = fields.Integer(required=False, allow_none=True)
    min_stay_arrival = fields.Integer(required=False, allow_none=True)
    max_stay = fields.Integer(required=False, allow_none=True)
    max_stay_arrival = fields.Integer(required=False, allow_none=True)
    closed = fields.Boolean(required=False, allow_none=True)
    closed_departure = fields.Boolean(required=False, allow_none=True)
    closed_arrival = fields.Boolean(required=False, allow_none=True)
    quota = fields.Integer(required=False, allow_none=True)
    max_avail = fields.Integer(required=False, allow_none=True)
    room_type_id = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
