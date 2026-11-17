# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class PmsBaseCase(TransactionCase):
    """Common setup for all PMS Base tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Owner partner
        cls.owner = cls.env["res.partner"].create(
            {"name": "Test Owner", "email": "owner@test.com"}
        )

        # Room types (from data)
        cls.room_type_bed = cls.env.ref("pms_base.pms_room_type_bed")
        cls.room_type_bath = cls.env.ref("pms_base.pms_room_type_bath")
        cls.room_type_kitchen = cls.env.ref("pms_base.pms_room_type_kitchen")
        cls.room_type_living = cls.env.ref("pms_base.pms_room_type_living")
        cls.room_type_balcony = cls.env.ref("pms_base.pms_room_type_balcony")
        cls.room_type_patio = cls.env.ref("pms_base.pms_room_type_patio")
        cls.room_type_laundry = cls.env.ref("pms_base.pms_room_type_laundry")
        cls.room_type_parking = cls.env.ref("pms_base.pms_room_type_parking_lot")
        cls.room_type_pets = cls.env.ref("pms_base.pms_room_type_pets")
        cls.room_type_half_bath = cls.env.ref("pms_base.pms_room_type_half_bath")
        cls.room_type_dining = cls.env.ref("pms_base.pms_room_type_dining")

        # Amenity types (from data)
        cls.amenity_type_laundry = cls.env.ref("pms_base.pms_amenity_type_3")
        cls.amenity_type_parking = cls.env.ref("pms_base.pms_amenity_type_4")
        cls.amenity_type_pets = cls.env.ref("pms_base.pms_amenity_type_5")
        cls.amenity_type_connectivity = cls.env.ref("pms_base.pms_amenity_type_1")

        # Default team
        cls.team = cls.env.ref("pms_base.pms_team_default")

        # A basic property used in many tests
        cls.property = cls.env["pms.property"].create(
            {
                "name": "Test Property",
                "owner_id": cls.owner.id,
                "tz": "UTC",
                "team_id": cls.team.id,
            }
        )
