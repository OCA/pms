# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import fields, models

from odoo.addons.http_routing.models.ir_http import slug


class PmsRoomType(models.Model):
    _inherit = "pms.room.type"

    short_description = fields.Text(string="Short Description", translate=True)
    long_description = fields.Html(
        string="Long Description",
        sanitize_style=True,
        translate=True,
    )
    website_url = fields.Char(compute="_compute_website_url_room_type")

    def _compute_website_url_room_type(self):
        """pms.room.type delegates product.product, meaning we inherit
        website.published.multi.mixin. For some reason, overwriting
        _compute_website_url doesn't work, so we instead define our own compute
        method.

        TODO: Research the above problem.
        """
        for room_type in self:
            if room_type.id:
                room_type.website_url = "/room/%s" % slug(room_type)
