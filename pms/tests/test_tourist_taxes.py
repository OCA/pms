import datetime

from odoo import fields
from odoo.tests.common import TransactionCase


class TestTouristTaxes(TransactionCase):
    def setUpClass(self):
        super().setUpClass()
        self.product_tourist_tax = self.env["product.product"].create(
            {
                "name": "Tourist Tax",
                "is_tourist_tax": True,
                "touristic_calculation": "occupancy",
                "occupancy_domain": "[('state', '!=', 'cancel')]",
                "nights_domain": "[('state', '!=', 'cancel')]",
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Test Room Type",
                "product_id": self.env["product.product"]
                .create(
                    {
                        "name": "Room Product",
                        "type": "service",
                    }
                )
                .id,
            }
        )
        self.room = self.env["pms.room"].create(
            {
                "name": "Test Room",
                "room_type_id": self.room_type.id,
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner.id,
                "room_type_id": self.room_type.id,
                "checkin": fields.Date.today(),
                "checkout": fields.Date.today() + datetime.timedelta(days=2),
                "adults": 2,
            }
        )

    def test_add_tourist_tax_service(self):
        """
        Test that a tourist tax service is created when adding a reservation.
        Steps:
        1. Add a tourist tax service to the reservation.
        2. Search for the created service.
        3. Assert that the service is created and the quantity is correct.
        """
        self.reservation._add_tourist_tax_service()
        service = self.env["pms.service"].search(
            [
                ("reservation_id", "=", self.reservation.id),
                ("product_id", "=", self.product_tourist_tax.id),
            ]
        )
        self.assertEqual(len(service), 1, "Tourist tax service should be created")
        self.assertEqual(service.quantity, 2, "Tourist tax quantity should be 2")

    def test_update_tourist_tax_service(self):
        """
        Test that a tourist tax service is updated when modifying the reservation.
        Steps:
        1. Add a tourist tax service to the reservation.
        2. Update the number of adults in the reservation.
        3. Update the tourist tax service.
        4. Search for the updated service.
        5. Assert that the service is updated and the quantity is correct.
        """
        self.reservation._add_tourist_tax_service()
        self.reservation.adults = 3
        self.reservation._update_tourist_tax_service()
        service = self.env["pms.service"].search(
            [
                ("reservation_id", "=", self.reservation.id),
                ("product_id", "=", self.product_tourist_tax.id),
            ]
        )
        self.assertEqual(len(service), 1, "Tourist tax service should be updated")
        self.assertEqual(
            service.quantity, 3, "Tourist tax quantity should be updated to 3"
        )

    def test_no_tourist_tax_service_when_quantity_zero(self):
        """
        Test that no tourist tax service is created when the quantity is zero.
        Steps:
        1. Set the tourist tax calculation to 'occupancyandnights'.
        2. Add a tourist tax service to the reservation.
        3. Search for the created service.
        4. Assert that no service is created.
        """
        self.product_tourist_tax.touristic_calculation = "occupancyandnights"
        self.reservation._add_tourist_tax_service()
        service = self.env["pms.service"].search(
            [
                ("reservation_id", "=", self.reservation.id),
                ("product_id", "=", self.product_tourist_tax.id),
            ]
        )
        self.assertEqual(
            len(service),
            0,
            "Tourist tax service should not be created when quantity is zero",
        )

    def test_remove_tourist_tax_service_when_quantity_zero(self):
        """
        Test that a tourist tax service is removed when the quantity becomes zero.
        Steps:
        1. Set the tourist tax calculation to 'occupancy'.
        2. Add a tourist tax service to the reservation.
        3. Update the number of adults in the reservation to zero.
        4. Update the tourist tax service.
        5. Search for the updated service.
        6. Assert that the service is removed.
        """
        self.product_tourist_tax.touristic_calculation = "occupancy"
        self.reservation._add_tourist_tax_service()
        self.reservation.adults = 0
        self.reservation._update_tourist_tax_service()
        service = self.env["pms.service"].search(
            [
                ("reservation_id", "=", self.reservation.id),
                ("product_id", "=", self.product_tourist_tax.id),
            ]
        )
        self.assertEqual(
            len(service),
            0,
            "Tourist tax service should be removed when quantity is zero",
        )
