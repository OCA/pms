from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel

class PmsReportInfo(Datamodel):
    _name = "pms.report.info"
    pdf = fields.String(required=False, allow_none=True)
