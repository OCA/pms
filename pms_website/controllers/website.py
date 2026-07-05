# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.fields import Domain
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL, Website


class Website(Website):
    _properties_per_page = 12

    def _get_pms_display_flags(self):
        groups = request.env["res.groups"].sudo()
        user_group = groups.env.ref("base.group_user")
        return {
            "show_rooms": groups.env.ref("pms_base.group_pms_show_room")
            in user_group.implied_ids,
            "show_amenities": groups.env.ref("pms_base.group_pms_show_amenity")
            in user_group.implied_ids,
            "show_services": groups.env.ref("pms_base.group_pms_show_service")
            in user_group.implied_ids,
        }

    def _get_published_properties_domain(self):
        return Domain.AND(
            [
                [("is_published", "=", True)],
                request.website.website_domain(),
            ]
        )

    def _get_properties_filter_domain(
        self, city=None, bedrooms=None, category=None, tag=None, show_rooms=True
    ):
        domain = []
        if city:
            domain.append(("city", "=", city))
        if bedrooms and show_rooms:
            domain.append(("qty_bedroom", "=", int(bedrooms)))
        if category:
            domain.append(("property_category_ids", "in", [int(category)]))
        if tag:
            domain.append(("tag_ids", "in", [int(tag)]))
        return domain

    def _get_properties_filter_options(self, base_domain, show_rooms=True):
        Property = request.env["pms.property"]
        properties = Property.sudo().search(base_domain, order="city, name")
        cities = sorted({city for city in properties.mapped("city") if city})
        bedrooms = []
        if show_rooms:
            bedrooms = sorted(
                {qty for qty in properties.mapped("qty_bedroom") if qty},
                reverse=True,
            )
        categories = properties.mapped("property_category_ids").sorted("name")
        tags = properties.mapped("tag_ids").sorted("name")
        return {
            "cities": cities,
            "bedrooms": bedrooms,
            "categories": categories,
            "tags": tags,
        }

    def _prepare_properties_values(
        self, page=0, city=None, bedrooms=None, category=None, tag=None, **kwargs
    ):
        Property = request.env["pms.property"]
        base_domain = self._get_published_properties_domain()
        display_flags = self._get_pms_display_flags()
        filter_domain = self._get_properties_filter_domain(
            city=city,
            bedrooms=bedrooms,
            category=category,
            tag=tag,
            show_rooms=display_flags["show_rooms"],
        )
        domain = Domain.AND([base_domain, filter_domain])
        properties_count = Property.sudo().search_count(domain)
        url_args = {
            key: value
            for key, value in {
                "city": city,
                "bedrooms": bedrooms,
                "category": category,
                "tag": tag,
            }.items()
            if value
        }
        pager = request.website.pager(
            url="/properties",
            url_args=url_args,
            total=properties_count,
            page=page,
            step=self._properties_per_page,
        )
        properties = Property.sudo().search(
            domain,
            limit=self._properties_per_page,
            offset=pager["offset"],
            order="name",
        )
        filter_options = self._get_properties_filter_options(
            base_domain, show_rooms=display_flags["show_rooms"]
        )
        return {
            "properties": properties,
            "pager": pager,
            "cities": filter_options["cities"],
            "bedrooms_options": filter_options["bedrooms"],
            "categories": filter_options["categories"],
            "tags": filter_options["tags"],
            "selected_city": city or "",
            "selected_bedrooms": bedrooms or "",
            "selected_category": category or "",
            "selected_tag": tag or "",
            **display_flags,
        }

    @http.route(
        ["/properties", "/properties/page/<int:page>"],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def properties(
        self, page=0, city=None, bedrooms=None, category=None, tag=None, **kwargs
    ):
        return request.render(
            "pms_website.properties",
            self._prepare_properties_values(
                page=page,
                city=city,
                bedrooms=bedrooms,
                category=category,
                tag=tag,
                **kwargs,
            ),
        )

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
        keep = QueryURL("/properties")
        return {
            "property": pms_property,
            "main_object": pms_property,
            "keep": keep,
            **self._get_pms_display_flags(),
        }
