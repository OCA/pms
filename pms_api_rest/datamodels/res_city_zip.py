from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class ResCityZipInfo(Datamodel):
    _name = "res.city.zip.info"
    cityId = fields.String(required=False, allow_none=True)
    stateId = fields.String(required=False, allow_none=True)
    countryId = fields.String(required=False, allow_none=True)
