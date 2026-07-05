# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from werkzeug.exceptions import NotFound

from odoo.exceptions import UserError
from odoo.tests.common import HttpCase

from odoo.addons.pms_base.tests.common import PmsBaseCase
from odoo.addons.pms_website.controllers.website import Website


class TestPmsWebsite(PmsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].create({"name": "Test Site"})
        cls.property.write({"website_id": cls.website.id, "is_published": True})
        cls.property.partner_id.write(
            {
                "street": "1 Main St",
                "city": "Testville",
                "partner_latitude": 33.0,
                "partner_longitude": -112.0,
            }
        )

    def test_property_website_fields(self):
        self.assertEqual(self.property.website_id, self.website)
        self.assertTrue(self.property.is_published)

    def test_property_website_url(self):
        self.property._compute_website_url()
        self.assertIn("/property/", self.property.website_url)

    def test_property_website_url_without_id(self):
        prop = self.env["pms.property"].new({"name": "Draft"})
        prop._compute_website_url()
        self.assertFalse(prop.id)

    def test_property_google_map_link(self):
        link = self.property.google_map_link()
        self.assertIn("maps.google.com", link)
        self.assertIn("33.0", link)

    def test_amenity_is_main_amenity(self):
        amenity = self.env["pms.amenity"].create({"name": "WiFi"})
        self.assertFalse(amenity.is_main_amenity)
        amenity.is_main_amenity = True
        self.assertTrue(amenity.is_main_amenity)

    def test_website_category_hierarchy(self):
        parent = self.env["pms.website.category"].create({"name": "Beach"})
        child = self.env["pms.website.category"].create(
            {"name": "Villas", "parent_id": parent.id}
        )
        self.assertIn("Beach", child.display_name)
        child._compute_parents_and_self_new()
        self.assertIn(parent, child.parents_and_self)

    def test_website_category_display_name(self):
        parent = self.env["pms.website.category"].create({"name": "Coast"})
        child = self.env["pms.website.category"].create(
            {"name": "Suites", "parent_id": parent.id}
        )
        child._compute_parents_and_self_new()
        child._compute_display_name()
        self.assertEqual(child.display_name, "Coast / Suites")

    def test_website_category_check_parent_id_cycle(self):
        category = self.env["pms.website.category"].create({"name": "Cat"})
        with patch.object(type(category), "_has_cycle", return_value=True):
            with self.assertRaises(ValueError):
                category.check_parent_id()

    def test_website_category_recursion(self):
        parent = self.env["pms.website.category"].create({"name": "Root"})
        child = self.env["pms.website.category"].create(
            {"name": "Child", "parent_id": parent.id}
        )
        with self.assertRaises(UserError):
            parent.parent_id = child

    def test_property_category_link(self):
        category = self.env["pms.website.category"].create({"name": "Luxury"})
        self.property.property_category_ids = category
        self.assertIn(self.property, category.property_ids)

    def test_property_website_description_fields(self):
        self.property.write(
            {
                "website_description1": "<p>Main description</p>",
                "website_description2": "<p>Secondary description</p>",
            }
        )
        self.assertIn("Main description", self.property.website_description1)
        self.assertIn("Secondary description", self.property.website_description2)

    def test_website_category_parent_path(self):
        parent = self.env["pms.website.category"].create({"name": "Region"})
        child = self.env["pms.website.category"].create(
            {"name": "District", "parent_id": parent.id}
        )
        self.assertTrue(child.parent_path)
        child._compute_parents_and_self_new()
        self.assertIn(parent, child.parents_and_self)
        self.assertIn(child, child.parents_and_self)

    def test_website_category_check_parent_id_valid(self):
        category = self.env["pms.website.category"].create({"name": "Valid"})
        category.check_parent_id()

    def test_website_category_without_parent_path(self):
        category = self.env["pms.website.category"].new({"name": "Standalone"})
        category._compute_parents_and_self_new()
        self.assertEqual(category.parents_and_self, category)


class TestPmsWebsiteController(PmsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].create({"name": "Test Site"})
        cls.property.write({"website_id": cls.website.id, "is_published": True})

    @contextmanager
    def _mock_request(self, website_module, render=False):
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_website = MagicMock()
        mock_website.website_domain.return_value = [
            ("website_id", "in", (False, self.website.id))
        ]
        mock_website.pager.return_value = {
            "page_count": 1,
            "offset": 0,
            "page": {"num": 0},
        }
        mock_request.website = mock_website
        if render:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.get_data.return_value = b"page"
            mock_request.render.return_value = mock_response
        with patch.object(website_module, "request", mock_request):
            yield mock_request

    def test_prepare_property_values(self):
        from ..controllers import website as website_module

        controller = Website()
        with self._mock_request(website_module):
            values = controller._prepare_property_values(
                self.property, "category", "search", extra=True
            )
        self.assertEqual(values["property"], self.property)
        self.assertEqual(values["main_object"], self.property)
        self.assertEqual(values["keep"].path, "/properties")
        self.assertIn("show_rooms", values)
        self.assertIn("show_amenities", values)
        self.assertIn("show_services", values)

    def test_get_pms_display_flags(self):
        from ..controllers import website as website_module

        controller = Website()
        user_group = self.env.ref("base.group_user")
        room_group = self.env.ref("pms_base.group_pms_show_room")
        user_group.write({"implied_ids": [(4, room_group.id)]})
        with self._mock_request(website_module):
            flags = controller._get_pms_display_flags()
        self.assertTrue(flags["show_rooms"])
        user_group.write({"implied_ids": [(3, room_group.id)]})
        with self._mock_request(website_module):
            flags = controller._get_pms_display_flags()
        self.assertFalse(flags["show_rooms"])

    def test_get_pms_display_flags_amenities_and_services(self):
        from ..controllers import website as website_module

        controller = Website()
        user_group = self.env.ref("base.group_user")
        amenity_group = self.env.ref("pms_base.group_pms_show_amenity")
        service_group = self.env.ref("pms_base.group_pms_show_service")
        user_group.write(
            {
                "implied_ids": [
                    (4, amenity_group.id),
                    (4, service_group.id),
                ]
            }
        )
        with self._mock_request(website_module):
            flags = controller._get_pms_display_flags()
        self.assertTrue(flags["show_amenities"])
        self.assertTrue(flags["show_services"])

    def test_get_published_properties_domain(self):
        from ..controllers import website as website_module

        controller = Website()
        with self._mock_request(website_module):
            domain = controller._get_published_properties_domain()
            published = self.env["pms.property"].sudo().search(domain)
        self.assertIn(self.property, published)

    def test_get_properties_filter_domain(self):
        controller = Website()
        category = self.env["pms.website.category"].create({"name": "Coastal"})
        tag = self.env["pms.tag"].create({"name": "Featured"})
        domain = controller._get_properties_filter_domain(
            city="Boston",
            bedrooms="2",
            category=str(category.id),
            tag=str(tag.id),
        )
        self.assertEqual(
            domain,
            [
                ("city", "=", "Boston"),
                ("qty_bedroom", "=", 2),
                ("property_category_ids", "in", [category.id]),
                ("tag_ids", "in", [tag.id]),
            ],
        )
        self.assertEqual(
            controller._get_properties_filter_domain(bedrooms="2", show_rooms=False),
            [],
        )
        self.assertEqual(controller._get_properties_filter_domain(), [])

    def test_get_properties_filter_options(self):
        from ..controllers import website as website_module

        self.property.write({"city": "Alpha City"})
        category = self.env["pms.website.category"].create({"name": "Coastal"})
        tag = self.env["pms.tag"].create({"name": "Vacation"})
        self.property.write(
            {
                "property_category_ids": [(4, category.id)],
                "tag_ids": [(4, tag.id)],
            }
        )
        self.env["pms.room"].create(
            {
                "name": "Bedroom",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        controller = Website()
        with self._mock_request(website_module):
            options = controller._get_properties_filter_options(
                controller._get_published_properties_domain()
            )
        self.assertIn("Alpha City", options["cities"])
        self.assertIn(self.property.qty_bedroom, options["bedrooms"])
        self.assertIn(category, options["categories"])
        self.assertIn(tag, options["tags"])

    def test_get_properties_filter_options_hide_rooms(self):
        from ..controllers import website as website_module

        self.env["pms.room"].create(
            {
                "name": "Bedroom",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        controller = Website()
        with self._mock_request(website_module):
            options = controller._get_properties_filter_options(
                controller._get_published_properties_domain(),
                show_rooms=False,
            )
        self.assertEqual(options["bedrooms"], [])

    def test_product_page_not_found(self):
        controller = Website()
        with patch.object(
            type(self.property),
            "can_access_from_current_website",
            return_value=False,
        ):
            with self.assertRaises(NotFound):
                controller.product(self.property)

    def test_product_page_render(self):
        from ..controllers import website as website_module

        controller = Website()
        with patch("odoo.http.Response.load", lambda result: result):
            with self._mock_request(website_module, render=True) as mock_request:
                with patch.object(
                    type(self.property),
                    "can_access_from_current_website",
                    return_value=True,
                ):
                    result = controller.product(
                        self.property, category="category", search="search"
                    )
                mock_request.render.assert_called_once()
                args, _kwargs = mock_request.render.call_args
                self.assertEqual(args[0], "pms_website.property")
                self.assertEqual(args[1]["property"], self.property)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.get_data(), b"page")

    def test_properties_list_render(self):
        from ..controllers import website as website_module

        controller = Website()
        with patch("odoo.http.Response.load", lambda result: result):
            with self._mock_request(website_module, render=True) as mock_request:
                result = controller.properties()
                mock_request.render.assert_called_once()
                args, _kwargs = mock_request.render.call_args
                self.assertEqual(args[0], "pms_website.properties")
                self.assertIn(self.property, args[1]["properties"])
                self.assertIn("cities", args[1])
                self.assertEqual(result.status_code, 200)

    def test_properties_filter_by_city(self):
        from ..controllers import website as website_module

        self.property.write({"city": "Filterville"})
        controller = Website()
        with self._mock_request(website_module):
            values = controller._prepare_properties_values(city="Filterville")
            self.assertIn(self.property, values["properties"])
            values = controller._prepare_properties_values(city="Other City")
            self.assertNotIn(self.property, values["properties"])

    def test_properties_filter_by_bedrooms(self):
        from ..controllers import website as website_module

        user_group = self.env.ref("base.group_user")
        user_group.write(
            {"implied_ids": [(4, self.env.ref("pms_base.group_pms_show_room").id)]}
        )
        self.env["pms.room"].create(
            {
                "name": "Extra Bedroom",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        controller = Website()
        with self._mock_request(website_module):
            values = controller._prepare_properties_values(
                bedrooms=str(self.property.qty_bedroom)
            )
            self.assertIn(self.property, values["properties"])

    def test_properties_filter_by_category(self):
        from ..controllers import website as website_module

        category = self.env["pms.website.category"].create({"name": "Beach"})
        other_category = self.env["pms.website.category"].create({"name": "Mountain"})
        self.property.property_category_ids = category
        other_property = self.env["pms.property"].create(
            {
                "name": "Mountain Property",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "team_id": self.team.id,
                "website_id": self.website.id,
                "is_published": True,
                "property_category_ids": [(4, other_category.id)],
            }
        )
        controller = Website()
        with self._mock_request(website_module):
            values = controller._prepare_properties_values(category=str(category.id))
            self.assertIn(self.property, values["properties"])
            self.assertNotIn(other_property, values["properties"])
            self.assertEqual(values["selected_category"], str(category.id))

    def test_properties_filter_by_tag(self):
        from ..controllers import website as website_module

        tag = self.env["pms.tag"].create({"name": "Featured"})
        other_tag = self.env["pms.tag"].create({"name": "Standard"})
        self.property.tag_ids = tag
        other_property = self.env["pms.property"].create(
            {
                "name": "Standard Property",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "team_id": self.team.id,
                "website_id": self.website.id,
                "is_published": True,
                "tag_ids": [(4, other_tag.id)],
            }
        )
        controller = Website()
        with self._mock_request(website_module):
            values = controller._prepare_properties_values(tag=str(tag.id))
            self.assertIn(self.property, values["properties"])
            self.assertNotIn(other_property, values["properties"])
            self.assertEqual(values["selected_tag"], str(tag.id))

    def test_properties_excludes_unpublished(self):
        from ..controllers import website as website_module

        self.property.is_published = False
        controller = Website()
        with self._mock_request(website_module):
            values = controller._prepare_properties_values()
        self.assertNotIn(self.property, values["properties"])

    def test_properties_bedrooms_filter_ignored_when_rooms_hidden(self):
        from ..controllers import website as website_module

        user_group = self.env.ref("base.group_user")
        user_group.write(
            {"implied_ids": [(3, self.env.ref("pms_base.group_pms_show_room").id)]}
        )
        self.env["pms.room"].create(
            {
                "name": "Bedroom",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        controller = Website()
        with self._mock_request(website_module):
            values = controller._prepare_properties_values(bedrooms="99")
        self.assertIn(self.property, values["properties"])
        self.assertEqual(values["bedrooms_options"], [])


class TestPmsWebsiteHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = cls.env["res.partner"].create({"name": "Test Owner"})
        cls.team = cls.env.ref("pms_base.pms_team_default")
        cls.website = cls.env.ref("website.default_website")
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.service_product = cls.env["product.product"].create(
            {"name": "Internet", "type": "service"}
        )
        cls.property = cls.env["pms.property"].create(
            {
                "name": "Published Property",
                "owner_id": cls.owner.id,
                "tz": "UTC",
                "team_id": cls.team.id,
                "is_published": True,
                "website_id": cls.website.id,
            }
        )
        cls.env.ref("base.group_user").write(
            {
                "implied_ids": [
                    (4, cls.env.ref("pms_base.group_pms_show_room").id),
                    (4, cls.env.ref("pms_base.group_pms_show_amenity").id),
                    (4, cls.env.ref("pms_base.group_pms_show_service").id),
                ]
            }
        )

    def _create_published_property(self, name, city):
        return self.env["pms.property"].create(
            {
                "name": name,
                "owner_id": self.owner.id,
                "tz": "UTC",
                "team_id": self.team.id,
                "city": city,
                "is_published": True,
                "website_id": self.website.id,
            }
        )

    def test_property_page_public(self):
        response = self.url_open(self.property.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Published Property", response.content)

    def test_property_page_amenities(self):
        main_amenity = self.env["pms.amenity"].create(
            {"name": "Wi-Fi", "is_main_amenity": True}
        )
        self.env["pms.amenity"].create({"name": "Shampoo", "is_main_amenity": False})
        property_rec = self._create_published_property("Amenity Property", "Boston")
        property_rec.amenity_ids = main_amenity
        response = self.url_open(property_rec.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Amenities", response.content)
        self.assertIn(b"Wi-Fi", response.content)
        self.assertIn(b"Explore all amenities", response.content)
        self.assertIn(b"propertyAmenitiesModal", response.content)

    def test_properties_page_public(self):
        self._create_published_property("City Property A", "New York")
        self._create_published_property("City Property B", "Chicago")
        response = self.url_open("/properties")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"City Property A", response.content)
        self.assertIn(b"City Property B", response.content)
        self.assertIn(b'name="city"', response.content)
        self.assertIn(b'name="bedrooms"', response.content)

    def test_property_page_contact_and_breadcrumb(self):
        response = self.url_open(self.property.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Contact us", response.content)
        self.assertIn(b'href="/contactus"', response.content)
        self.assertIn(b'href="/properties"', response.content)
        self.assertIn(b"Properties", response.content)

    def test_property_page_hides_sections_when_features_disabled(self):
        user_group = self.env.ref("base.group_user")
        user_group.write(
            {
                "implied_ids": [
                    (4, self.env.ref("pms_base.group_pms_show_amenity").id),
                    (
                        3,
                        self.env.ref("pms_base.group_pms_show_service").id,
                    ),
                    (
                        3,
                        self.env.ref("pms_base.group_pms_show_room").id,
                    ),
                ]
            }
        )
        property_rec = self._create_published_property("Filtered Property", "Denver")
        property_rec.amenity_ids = self.env["pms.amenity"].create(
            {"name": "Pool", "is_main_amenity": True}
        )
        self.env["pms.service"].create(
            {
                "name": self.service_product.id,
                "property_id": property_rec.id,
                "vendor_id": self.vendor.id,
                "icon": "fa-wifi",
            }
        )
        self.env["pms.room"].create(
            {
                "name": "Bedroom",
                "property_id": property_rec.id,
                "type_id": self.env.ref("pms_base.pms_room_type_bed").id,
            }
        )
        response = self.url_open(property_rec.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<h5 class="mb-3">Services</h5>', response.content)
        self.assertNotIn(b"Bedrooms", response.content)
        self.assertIn(b"Amenities", response.content)

    def test_properties_page_filter_by_city(self):
        self._create_published_property("New York Property", "New York")
        self._create_published_property("Chicago Property", "Chicago")
        response = self.url_open("/properties?city=New+York")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"New York Property", response.content)
        self.assertNotIn(b"Chicago Property", response.content)

    def test_property_page_services(self):
        property_rec = self._create_published_property("Service Property", "Austin")
        self.env["pms.service"].create(
            {
                "name": self.service_product.id,
                "property_id": property_rec.id,
                "vendor_id": self.vendor.id,
                "icon": "fa-wifi",
            }
        )
        response = self.url_open(property_rec.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<h5 class="mb-3">Services</h5>', response.content)

    def test_properties_page_filter_by_category(self):
        category = self.env["pms.website.category"].create({"name": "Beach"})
        beach_property = self._create_published_property("Beach House", "Miami")
        beach_property.property_category_ids = category
        self._create_published_property("City Loft", "Seattle")
        response = self.url_open(f"/properties?category={category.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Beach House", response.content)
        self.assertNotIn(b"City Loft", response.content)

    def test_properties_page_filter_by_tag(self):
        tag = self.env["pms.tag"].create({"name": "Featured"})
        featured_property = self._create_published_property("Featured Home", "Portland")
        featured_property.tag_ids = tag
        self._create_published_property("Regular Home", "Dallas")
        response = self.url_open(f"/properties?tag={tag.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Featured Home", response.content)
        self.assertNotIn(b"Regular Home", response.content)
