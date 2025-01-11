from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access


class PmsClosureReasonService(Component):
    _inherit = "base.rest.service"
    _name = "pms.closure.reason.service"
    _usage = "room-closure-reasons"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.room.closure.reason.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_closure_reasons(self):
        closure_reasons_result = []
        PmsRoomClosureReasonInfo = self.env.datamodels["pms.room.closure.reason.info"]
        closure_reasons = self.env["room.closure.reason"].sudo().search([])
        pms_api_check_access(user=self.env.user, records=closure_reasons)
        for clousure_reason in closure_reasons:
            closure_reasons_result.append(
                PmsRoomClosureReasonInfo(
                    id=clousure_reason.id,
                    name=clousure_reason.name,
                    description=clousure_reason.description or None,
                )
            )
        return closure_reasons_result
