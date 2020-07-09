# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _
from odoo.http import request
from odoo.exceptions import MissingError


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super().session_info()
        user = request.env.user
        display_switch_pms_menu = len(user.pms_property_ids) > 1
        # TODO: limit properties to the current company?
        # or switch company automatically
        res['pms_property_id'] = request.env.user.pms_property_id.id if \
            request.session.uid else None
        res['user_properties'] = {
            'current_property': (user.pms_property_id.id, user.pms_property_id.name),
            'allowed_properties': [
                (property.id, property.name) for property in user.pms_property_ids
                ]
            } if display_switch_pms_menu else False
        if user.pms_property_id.company_id in user.company_ids:
            user.company_id = user.pms_property_id.company_id
            res['company_id'] = user.pms_property_id.company_id.id
        else:
            return res #TODO Review method
            raise MissingError(
                _("Wrong property and company access settings for this user. "
                  "Please review property and company for user %s") % user.name)

        return res
