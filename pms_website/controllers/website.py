# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL, Website


class Website(Website):
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
            "pms_website.property",
            self._prepare_property_values(pms_property, category, search, **kwargs),
        )

    def _prepare_property_values(self, pms_property, category, search, **kwargs):
        keep = QueryURL("/property")
        return {
            "property": pms_property,
            "main_object": pms_property,
            # 'search': search,
            # 'category': category,
            # 'pricelist': pricelist,
            # 'attrib_values': attrib_values,
            # 'attrib_set': attrib_set,
            "keep": keep,
            # 'categories': categs,
            # 'product': product,
            # 'add_qty': add_qty,
            # 'view_track': view_track,
        }
