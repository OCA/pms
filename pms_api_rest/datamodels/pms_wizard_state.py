from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel

class PmsWizardStateInfo(Datamodel):
    _name = "pms.wizard.state.info"
    code = fields.String(required=True, allow_none=False)
    title = fields.String(required=False, allow_none=True)
    text = fields.String(required=False, allow_none=True)
