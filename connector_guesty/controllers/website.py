# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.pms_website.controllers.website import Website


class CasaiWebsite(Website):
    @http.route(
        ['/property/<model("pms.property"):pms_property>'],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def product(self, pms_property, category="", search="", **kwargs):
        if not pms_property.can_access_from_current_website():
            raise NotFound()
        return request.render(
            "connector_guesty.property_casai_website",
            self._prepare_property_values(pms_property, category, search, **kwargs),
        )
