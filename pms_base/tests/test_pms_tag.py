# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from psycopg2 import IntegrityError

from odoo.tests.common import mute_logger

from .common import PmsBaseCase


class TestPmsTag(PmsBaseCase):
    """Tests for pms.tag model."""

    def test_create_tag(self):
        """A tag can be created with a name."""
        tag = self.env["pms.tag"].create({"name": "Sea View"})
        self.assertEqual(tag.name, "Sea View")
        self.assertEqual(tag.full_name, "Sea View")

    def test_full_name_without_parent(self):
        """full_name equals name when there is no parent."""
        tag = self.env["pms.tag"].create({"name": "Top Level"})
        self.assertEqual(tag.full_name, "Top Level")

    def test_full_name_with_parent(self):
        """full_name is 'Parent/Child' when a parent is set."""
        parent = self.env["pms.tag"].create({"name": "Location"})
        child = self.env["pms.tag"].create({"name": "Beach", "parent_id": parent.id})
        self.assertEqual(child.full_name, "Location/Beach")

    def test_full_name_updates_on_parent_change(self):
        """full_name recomputes when the parent is changed."""
        parent1 = self.env["pms.tag"].create({"name": "Zone A"})
        parent2 = self.env["pms.tag"].create({"name": "Zone B"})
        child = self.env["pms.tag"].create({"name": "Room", "parent_id": parent1.id})
        self.assertEqual(child.full_name, "Zone A/Room")
        child.parent_id = parent2
        self.assertEqual(child.full_name, "Zone B/Room")

    def test_unique_name_constraint(self):
        """Creating two tags with the same name raises an error."""
        self.env["pms.tag"].create({"name": "Unique Tag"})
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env["pms.tag"].create({"name": "Unique Tag"})

    def test_tag_assigned_to_property(self):
        """A tag can be assigned to a property via tag_ids."""
        tag = self.env["pms.tag"].create({"name": "Premium"})
        self.property.write({"tag_ids": [tag.id]})
        self.assertIn(tag, self.property.tag_ids)

    def test_color_default(self):
        """Tags default to color index 10."""
        tag = self.env["pms.tag"].create({"name": "Color Default"})
        self.assertEqual(tag.color, 10)
