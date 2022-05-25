# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.pms_website.controllers.website import Website

DEMO_PICTURE_01 = "{}/pictures/14056/{}/{}.jpg".format(
    "https://dl6dfy55q2gns.cloudfront.net",
    "69af29bdd2d3b7621ca12d007fa640d1464437c7",
    "69af29bdd2d3b7621ca12d007fa640d1464437c",
)

DEMO_PICTURE_02 = "{}/pictures/14056/{}/{}.jpg".format(
    "https://dl6dfy55q2gns.cloudfront.net",
    "25e4599fe67112c1daab3981b897566bfd34612f",
    "25e4599fe67112c1daab3981b897566bfd34612",
)


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

    def _prepare_property_values(self, pms_property, category, search, **kwargs):
        rs = super()._prepare_property_values(pms_property, category, search, **kwargs)

        _MARKER_URL = "https://d1l56s2phyyu51.cloudfront.net/icons/marker-icon.png"
        _MAPS_URL = (
            "{}?{}&{}&{}5&{}&scale=1&format=png&{}&language=en&markers=icon:{}".format(
                "https://maps.googleapis.com/maps/api/staticmap",
                "key=",
                "zoom=1",
                "center=19.405035,-99.17485",
                "size=730x272",
                "maptype=roadmap",
                "{}|anchor:center|19.405035,-99.17485".format(_MARKER_URL),
            )
        )

        pictures = pms_property.website_picture_ids
        rs["slider_01"] = {"pictures": [a.url_large for a in pictures]}
        rs["section_id"] = {"picture": pms_property.front_picture.url_large}
        rs["map_picture"] = {"url": _MAPS_URL}
        return rs
