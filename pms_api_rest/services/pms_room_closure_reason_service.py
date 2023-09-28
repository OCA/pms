from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


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
        closure_reasons = []
        PmsRoomClosureReasonInfo = self.env.datamodels["pms.room.closure.reason.info"]
        for cl in self.env["room.closure.reason"].search([]):
            closure_reasons.append(
                PmsRoomClosureReasonInfo(
                    id=cl.id, name=cl.name, description=cl.description or None
                )
            )
        return closure_reasons
