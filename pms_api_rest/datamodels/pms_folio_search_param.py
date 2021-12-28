from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsFolioSearchParam(Datamodel):
    _name = "pms.folio.search.param"

    date_from = fields.String(required=False, allow_none=True)
    date_to = fields.String(required=False, allow_none=True)
