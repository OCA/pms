# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from .common import PmsBaseCase


class TestPmsProperty(PmsBaseCase):
    """Tests for pms.property model."""

    def test_create_sets_is_property(self):
        """create() must set is_property=True on the underlying partner."""
        prop = self.env["pms.property"].create(
            {"name": "Flag Test", "owner_id": self.owner.id, "tz": "UTC"}
        )
        self.assertTrue(prop.is_property)
        self.assertTrue(prop.partner_id.is_property)

    def test_display_name_without_ref(self):
        """display_name equals the property name when no ref is set."""
        prop = self.env["pms.property"].create(
            {"name": "Alpha", "owner_id": self.owner.id, "tz": "UTC"}
        )
        self.assertEqual(prop.display_name, "Alpha")

    def test_display_name_with_ref(self):
        """display_name prefixes the name with [ref] when ref is set."""
        prop = self.env["pms.property"].create(
            {"name": "Beta", "ref": "B-001", "owner_id": self.owner.id, "tz": "UTC"}
        )
        self.assertEqual(prop.display_name, "[B-001] Beta")

    def test_search_display_name_by_name(self):
        """_search_display_name finds a property by name."""
        prop = self.env["pms.property"].create(
            {"name": "Searchable", "owner_id": self.owner.id, "tz": "UTC"}
        )
        results = self.env["pms.property"].search(
            [("display_name", "ilike", "Searchable")]
        )
        self.assertIn(prop, results)

    def test_search_display_name_by_ref(self):
        """_search_display_name finds a property by its reference code."""
        prop = self.env["pms.property"].create(
            {
                "name": "RefProp",
                "ref": "XREF-999",
                "owner_id": self.owner.id,
                "tz": "UTC",
            }
        )
        results = self.env["pms.property"].search(
            [("display_name", "ilike", "XREF-999")]
        )
        self.assertIn(prop, results)

    def test_room_count(self):
        """room_count reflects the number of rooms linked to the property."""
        self.assertEqual(self.property.room_count, 0)
        self.env["pms.room"].create(
            {
                "name": "Room A",
                "property_id": self.property.id,
                "type_id": self.room_type_bed.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertEqual(self.property.room_count, 1)

    def test_child_property_count(self):
        """childs_property_count reflects the number of child properties."""
        self.assertEqual(self.property.childs_property_count, 0)
        child = self.env["pms.property"].create(
            {
                "name": "Child",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "parent_id": self.property.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertEqual(self.property.childs_property_count, 1)
        child.unlink()

    def test_action_view_childs_property_list(self):
        """action_view_childs_property_list returns a window action
        filtered to children."""
        child = self.env["pms.property"].create(
            {
                "name": "Child2",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "parent_id": self.property.id,
            }
        )
        action = self.property.action_view_childs_property_list()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertIn(child.id, action["domain"][0][2])

    def test_default_team_id(self):
        """A new property defaults to the default PMS team."""
        prop = self.env["pms.property"].create(
            {"name": "TeamDefault", "owner_id": self.owner.id, "tz": "UTC"}
        )
        self.assertEqual(prop.team_id, self.team)

    # --- Computed boolean fields from rooms ---

    def test_compute_balcony_true(self):
        """balcony becomes True when a room of balcony type is added."""
        self.env["pms.room"].create(
            {
                "name": "Balcony 1",
                "property_id": self.property.id,
                "type_id": self.room_type_balcony.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertTrue(self.property.balcony)

    def test_compute_balcony_false(self):
        """balcony is False when no balcony room exists."""
        prop = self.env["pms.property"].create(
            {"name": "NoBalcony", "owner_id": self.owner.id, "tz": "UTC"}
        )
        self.assertFalse(prop.balcony)

    def test_compute_terrace_true(self):
        """terrace becomes True when a patio room is added."""
        self.env["pms.room"].create(
            {
                "name": "Terrace 1",
                "property_id": self.property.id,
                "type_id": self.room_type_patio.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertTrue(self.property.terrace)

    def test_compute_laundry_room_via_room(self):
        """laundry_room becomes True when a laundry room is added."""
        self.env["pms.room"].create(
            {
                "name": "Laundry",
                "property_id": self.property.id,
                "type_id": self.room_type_laundry.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertTrue(self.property.laundry_room)

    def test_compute_laundry_room_via_amenity(self):
        """laundry_room becomes True when a laundry amenity is added."""
        amenity = self.env["pms.amenity"].create(
            {"name": "Laundry Service", "type_id": self.amenity_type_laundry.id}
        )
        prop = self.env["pms.property"].create(
            {
                "name": "LaundryAmenity",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "amenity_ids": [amenity.id],
            }
        )
        self.assertTrue(prop.laundry_room)

    def test_compute_parking_lot_via_room(self):
        """parking_lot becomes True when a parking room is added."""
        self.env["pms.room"].create(
            {
                "name": "Parking",
                "property_id": self.property.id,
                "type_id": self.room_type_parking.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertTrue(self.property.parking_lot)

    def test_compute_pets_via_amenity(self):
        """pets becomes True when a pets amenity is added."""
        amenity = self.env["pms.amenity"].create(
            {"name": "Pets allowed", "type_id": self.amenity_type_pets.id}
        )
        prop = self.env["pms.property"].create(
            {
                "name": "PetsAllowed",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "amenity_ids": [amenity.id],
            }
        )
        self.assertTrue(prop.pets)

    # --- Quantity computed fields ---

    def test_qty_bedroom(self):
        """qty_bedroom counts rooms of bedroom type."""
        for i in range(3):
            self.env["pms.room"].create(
                {
                    "name": f"Bed {i}",
                    "property_id": self.property.id,
                    "type_id": self.room_type_bed.id,
                }
            )
        self.property.invalidate_recordset()
        self.assertEqual(self.property.qty_bedroom, 3)

    def test_qty_kitchen(self):
        """qty_kitchen counts rooms of kitchen type."""
        self.env["pms.room"].create(
            {
                "name": "Kitchen",
                "property_id": self.property.id,
                "type_id": self.room_type_kitchen.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertEqual(self.property.qty_kitchen, 1)

    def test_qty_living_room(self):
        """qty_living_room counts rooms of living room type."""
        self.env["pms.room"].create(
            {
                "name": "Living",
                "property_id": self.property.id,
                "type_id": self.room_type_living.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertEqual(self.property.qty_living_room, 1)

    def test_qty_half_bathroom(self):
        """qty_half_bathroom counts rooms of half bathroom type."""
        self.env["pms.room"].create(
            {
                "name": "Half Bath",
                "property_id": self.property.id,
                "type_id": self.room_type_half_bath.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertEqual(self.property.qty_half_bathroom, 1)

    def test_qty_dining_room(self):
        """qty_dining_room counts rooms of dining room type."""
        self.env["pms.room"].create(
            {
                "name": "Dining",
                "property_id": self.property.id,
                "type_id": self.room_type_dining.id,
            }
        )
        self.property.invalidate_recordset()
        self.assertEqual(self.property.qty_dining_room, 1)

    def test_multi_create(self):
        """create() handles multiple records in one call (model_create_multi)."""
        vals_list = [
            {"name": f"Multi {i}", "owner_id": self.owner.id, "tz": "UTC"}
            for i in range(3)
        ]
        props = self.env["pms.property"].create(vals_list)
        self.assertEqual(len(props), 3)
        self.assertTrue(all(p.is_property for p in props))
