# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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

    def test_prepare_property_values(self):
        controller = Website()
        values = controller._prepare_property_values(
            self.property, "category", "search", extra=True
        )
        self.assertEqual(values["property"], self.property)
        self.assertEqual(values["main_object"], self.property)
        self.assertEqual(values["keep"].path, "/property")

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

        mock_request = MagicMock()
        mock_request.render.return_value = "page"
        controller = Website()
        with patch.object(website_module, "request", mock_request):
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


class TestPmsWebsiteHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = cls.env["res.partner"].create({"name": "Test Owner"})
        cls.team = cls.env.ref("pms_base.pms_team_default")
        cls.website = cls.env.ref("website.default_website")
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

    def test_property_page_public(self):
        response = self.url_open(self.property.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Published Property", response.content)
