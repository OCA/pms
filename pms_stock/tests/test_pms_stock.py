# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo.addons.pms_base.tests.common import PmsBaseCase


class TestPmsStock(PmsBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env["stock.location"].create(
            {"name": "Test Location", "usage": "internal"}
        )
        cls.property.write({"stock_location_id": cls.location.id})

    def _property_vals(self, name, **extra):
        return {
            "name": name,
            "owner_id": self.owner.id,
            "tz": "UTC",
            "team_id": self.team.id,
            **extra,
        }

    def test_property_stock_location(self):
        self.assertEqual(self.property.stock_location_id, self.location)

    def test_property_create_with_explicit_location(self):
        prop = self.env["pms.property"].create(
            self._property_vals("Explicit Location", stock_location_id=self.location.id)
        )
        self.assertEqual(prop.stock_location_id, self.location)

    def test_property_auto_stock_location(self):
        prop = self.env["pms.property"].create(
            self._property_vals("Auto Location Property")
        )
        self.assertTrue(prop.stock_location_id)
        self.assertEqual(prop.stock_location_id.name, prop.name)

    def test_property_auto_stock_location_parent(self):
        parent = self.env.ref("stock.stock_location_stock")
        prop = self.env["pms.property"].create(self._property_vals("Parented Property"))
        self.assertEqual(prop.stock_location_id.location_id, parent)
        self.assertEqual(prop.stock_location_id.usage, "internal")

    def test_property_batch_create_auto_stock_locations(self):
        props = self.env["pms.property"].create(
            [
                self._property_vals("Batch Property 1"),
                self._property_vals("Batch Property 2"),
            ]
        )
        for prop in props:
            self.assertTrue(prop.stock_location_id)
            self.assertEqual(prop.stock_location_id.name, prop.name)

    def test_property_rename_updates_stock_location(self):
        self.property.write({"name": "Renamed Property"})
        self.assertEqual(self.property.stock_location_id.name, "Renamed Property")

    def test_property_rename_creates_stock_location(self):
        prop = self.env["pms.property"].create(
            self._property_vals(
                "Write Location Property", stock_location_id=self.location.id
            )
        )
        prop.write({"stock_location_id": False, "name": "Renamed Without Location"})
        self.assertTrue(prop.stock_location_id)
        self.assertEqual(prop.stock_location_id.name, "Renamed Without Location")

    def test_create_stock_location_without_parent_on_create(self):
        with patch.object(self.env, "ref", return_value=False):
            prop = self.env["pms.property"].create(
                self._property_vals("No Parent Property")
            )
        self.assertFalse(prop.stock_location_id)

    def test_create_stock_location_without_parent_on_write(self):
        prop = self.env["pms.property"].create(
            self._property_vals("Write No Parent", stock_location_id=self.location.id)
        )
        with patch.object(self.env, "ref", return_value=False):
            prop.write({"stock_location_id": False, "name": "Renamed No Parent"})
        self.assertFalse(prop.stock_location_id)

    def test_create_stock_location_without_parent_direct(self):
        prop = self.env["pms.property"].create(
            self._property_vals("Direct No Parent", stock_location_id=self.location.id)
        )
        prop.write({"stock_location_id": False})
        with patch.object(self.env, "ref", return_value=False) as mock_ref:
            prop._create_stock_location()
            mock_ref.assert_called_once_with(
                "stock.stock_location_stock", raise_if_not_found=False
            )
        self.assertFalse(prop.stock_location_id)
