# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import MissingError
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super().session_info()
        user = request.env.user

        cids = request.httprequest.cookies.get("cids", str(user.company_id.id))
        company_ids = [int(cid) for cid in cids.split(",")]
        current_company_id = company_ids[0]

        pms_pids = request.httprequest.cookies.get(
            "pms_pids", str(user.pms_property_id.id)
        )
        pms_property_ids = [int(pid) for pid in pms_pids.split(",")]
        current_pms_property_id = pms_property_ids[0]
        current_pms_property = self.env["pms.property"].browse(current_pms_property_id)

        if current_pms_property.company_id.id != current_company_id:
            current_pms_property = self._get_default_active_pms_property(
                user, current_company_id
            )
            current_pms_property_id = current_pms_property.id

        allowed_properties = user.pms_property_ids.filtered(
            lambda p: p.company_id.id in company_ids
        )

        res.update(
            {
                # current_pms_property should be default_property
                "user_pms_properties": {
                    "current_pms_property": (
                        current_pms_property.id,
                        current_pms_property.name,
                    ),
                    # TODO: filter all properties based on
                    # the current set of active companies
                    "allowed_pms_properties": [
                        (property.id, property.name) for property in allowed_properties
                    ],
                },
                "display_switch_pms_property_menu": len(allowed_properties) > 1,
            }
        )
        # TODO: This user context update should be placed in other function ¿?
        res["user_context"].update(
            {
                "allowed_pms_property_ids": [
                    (property.id) for property in allowed_properties
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

    def _get_default_active_pms_property(self, user, current_company_id):
        """Get the default active pms property for the user.

        :param user: the user to get the user alloweds properties
        :param current_company: the current active company
        :return: the default active pms property
        """
        pms_property = user.pms_property_ids.filtered(
            lambda p: p.company_id.id == current_company_id
        )
        if not pms_property:
            raise MissingError(
                _(
                    "No active property for this user and company. "
                    "Please review property and company for user %s"
                )
                % user.name
            )
        return pms_property[0]
