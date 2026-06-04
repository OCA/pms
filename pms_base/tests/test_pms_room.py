# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.tests.common import mute_logger

from .common import PmsBaseCase


class TestPmsRoom(PmsBaseCase):
    """Tests for pms.room model."""

    def test_create_room(self):
        """A room can be created and linked to a property."""
        room = self.env["pms.room"].create(
            {
                "name": "Suite 101",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
                "capacity": 2,
                "area": 25.0,
            }
        )
        self.assertEqual(room.property_id, self.property)
        self.assertEqual(room.capacity, 2)
        self.assertEqual(room.area, 25.0)
        self.assertTrue(room.active)

    def test_unique_name_per_property(self):
        """Two rooms with the same name in the same property violate uniqueness."""
        self.env["pms.room"].create(
            {
                "name": "Duplex",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env["pms.room"].create(
                    {
                        "name": "Duplex",
                        "property_id": self.property.id,
                        "type_id": self.room_type_bath.id,
                    }
                )

    def test_same_name_different_property(self):
        """Two rooms with the same name in different properties are allowed."""
        other_property = self.env["pms.property"].create(
            {"name": "Other Prop", "owner_id": self.owner.id, "tz": "UTC"}
        )
        self.env["pms.room"].create(
            {
                "name": "Studio",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        room2 = self.env["pms.room"].create(
            {
                "name": "Studio",
                "property_id": other_property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        self.assertEqual(room2.name, "Studio")

    def test_archive_room(self):
        """A room can be archived (active=False)."""
        room = self.env["pms.room"].create(
            {
                "name": "Archive Me",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        room.action_archive()
        self.assertFalse(room.active)

    def test_room_order(self):
        """Rooms are ordered by sequence, type, name."""
        r1 = self.env["pms.room"].create(
            {
                "name": "Z Room",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
                "sequence": 1,
            }
        )
        r2 = self.env["pms.room"].create(
            {
                "name": "A Room",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
                "sequence": 2,
            }
        )
        rooms = self.env["pms.room"].search(
            [
                ("property_id", "=", self.property.id),
                ("name", "in", ["Z Room", "A Room"]),
            ]
        )
        self.assertEqual(rooms[0], r1)
        self.assertEqual(rooms[1], r2)
