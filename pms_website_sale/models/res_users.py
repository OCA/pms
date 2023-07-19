# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import api, models

class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def get_active_property_ids(self):
        # FIXME: This is a stupid and incorrect workaround to get the /room page
        # to load when you are not logged in. This method is called in
        # _compute_list_price in pms/models/product_template.py, which raises an
        # IndexError when the returned list is empty. It obviously needs to be
        # populated by _something_; I'm just not quite sure by what.
        #
        # The pms implementation of this method already includes a workaround
        # depending on a user's cookies, but I'm not quite sure what is
        # happening there, and there are no comments.
        if self.env.user == self.env.ref("base.public_user"):
            return self.env["pms.property"].search([]).ids
        else:
            return super().get_active_property_ids()
