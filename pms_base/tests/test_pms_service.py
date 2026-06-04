# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from psycopg2 import IntegrityError

from odoo.tests.common import mute_logger

from .common import PmsBaseCase


class TestPmsService(PmsBaseCase):
    """Tests for pms.service model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Cleaning", "type": "service"}
        )

    def _make_service(self, name=None, **kw):
        return self.env["pms.service"].create(
            {
                "name": self.product.id,
                "property_id": self.property.id,
                "vendor_id": self.vendor.id,
                **kw,
            }
        )

    def test_create_service(self):
        """A service can be created with required fields."""
        service = self._make_service(icon="fa-wifi")
        self.assertEqual(service.property_id, self.property)
        self.assertEqual(service.vendor_id, self.vendor)
        self.assertEqual(service.icon, "fa-wifi")
        self.assertTrue(service.active)

    def test_vendor_required(self):
        """Creating a service without vendor_id raises an error."""
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env["pms.service"].create(
                    {
                        "name": self.product.id,
                        "property_id": self.property.id,
                    }
                )

    def test_product_required(self):
        """Creating a service without name (product) raises an error."""
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env["pms.service"].create(
                    {
                        "property_id": self.property.id,
                        "vendor_id": self.vendor.id,
                    }
                )

    def test_archive_service(self):
        """A service can be archived (active=False)."""
        service = self._make_service()
        service.action_archive()
        self.assertFalse(service.active)

    def test_restore_service(self):
        """An archived service can be restored (active=True)."""
        service = self._make_service()
        service.action_archive()
        self.assertFalse(service.active)
        service.action_unarchive()
        self.assertTrue(service.active)

    def test_service_linked_to_property(self):
        """A service appears in property.service_ids."""
        service = self._make_service()
        self.assertIn(service, self.property.service_ids)

    def test_multiple_services_per_property(self):
        """A property can have multiple services."""
        product2 = self.env["product.product"].create(
            {"name": "Internet", "type": "service"}
        )
        s1 = self._make_service(icon="fa-home")
        s2 = self.env["pms.service"].create(
            {
                "name": product2.id,
                "property_id": self.property.id,
                "vendor_id": self.vendor.id,
                "icon": "fa-wifi",
            }
        )
        self.assertIn(s1, self.property.service_ids)
        self.assertIn(s2, self.property.service_ids)
