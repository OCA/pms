# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super().session_info()
        user = request.env.user
        res.update(
            {
                # current_pms_property should be default_property
                "user_pms_properties": {
                    "current_pms_property": (
                        user.pms_property_id.id,
                        user.pms_property_id.name,
                    ),
                    # TODO: filter all properties based on
                    # the current set of active companies
                    "allowed_pms_properties": [
                        (property.id, property.name)
                        for property in user.pms_property_ids
                    ],
                },
                "display_switch_pms_property_menu": len(user.pms_property_ids) > 1,
            }
        )
        # TODO: This user context update should be placed in other function ¿?
        res["user_context"].update(
            {
                "allowed_pms_property_ids": [
                    (property.id) for property in user.pms_property_ids
                ]
            }
        )
        # TODO: update current_company based on current_pms_property
        # if user.pms_property_id.company_id in user.company_ids:
        #     user.company_id = user.pms_property_id.company_id
        #     res['company_id'] = user.pms_property_id.company_id.id
        # else:
        #     raise MissingError(
        #         _("Wrong property and company access settings for this user. "
        #           "Please review property and company for user %s") % user.name)

        return res
