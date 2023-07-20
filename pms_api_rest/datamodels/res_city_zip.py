from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class ResCityZipSearchParam(Datamodel):
    _name = "res.city.zip.search.param"
    address = fields.String(required=False, allow_none=False)
class ResCityZipInfo(Datamodel):
    _name = "res.city.zip.info"
    resZipId = fields.Integer(required=False, allow_none=True)
    cityId = fields.String(required=False, allow_none=True)
    stateId = fields.Integer(required=False, allow_none=True)
    stateName = fields.String(required=False, allow_none=True)
    countryId = fields.Integer(required=False, allow_none=True)
    zipCode = fields.String(required=False, allow_none=True)
