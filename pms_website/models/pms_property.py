# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import werkzeug.urls

from odoo import fields, models
from odoo.tools.translate import html_translate

from odoo.addons.http_routing.models.ir_http import slug


class PmsProperty(models.Model):
    _name = "pms.property"
    _inherit = ["pms.property", "website.published.mixin", "website.multi.mixin"]

    def _compute_website_url(self):
        for pms_property in self:
            if pms_property.id:
                pms_property.website_url = "/property/%s" % slug(pms_property)

    def google_map_link(self):
        property_partner = self.sudo().partner_id
        property_partner.geo_localize()
        params = {
            "q": "%s, %s"
            % (property_partner.partner_latitude, property_partner.partner_longitude),
            "z": 10,
        }
        return "https://maps.google.com/maps?" + werkzeug.urls.url_encode(params)

    property_category_ids = fields.Many2many(
        string="Categories",
        required=False,
        comodel_name="pms.website.category",
        relation="property_category_rel",
    )
    website_description1 = fields.Html(
        "Property Description",
        sanitize_attributes=False,
        translate=html_translate,
        sanitize_form=False,
    )
    website_description2 = fields.Html(
        "Property Description 2",
        sanitize_attributes=False,
        translate=html_translate,
        sanitize_form=False,
    )
