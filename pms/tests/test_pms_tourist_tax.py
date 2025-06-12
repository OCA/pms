import datetime
import logging

from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import tagged

from .common import TestPms

_logger = logging.getLogger(__name__)


@tagged("tourist_tax")
class TestTouristTaxComputation(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
            }
        )

        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 101",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.partner_adult = cls.env["res.partner"].create(
            {
                "firstname": "Adult",
                "birthdate_date": "1990-01-01",
            }
        )

        cls.partner_child = cls.env["res.partner"].create(
            {
                "firstname": "Child",
                "birthdate_date": "2015-01-01",
            }
        )

        cls.sale_channel_direct = cls.env["pms.sale.channel"].create(
            {"name": "sale channel direct", "channel_type": "direct"}
        )

    @freeze_time("2025-07-01")
    def test_tourist_tax_lines_correctly_generated(self):
        """
        Test that the tourist tax service lines are correctly computed for 3 nights
        with one adult and one child (child is under age and excluded).
        """
        self.env["product.product"].create(
            {
                "name": "Tourist Tax",
                "list_price": 2.0,
                "is_tourist_tax": True,
                "per_person": True,
                "tourist_tax_date_start": "06-01",
                "tourist_tax_date_end": "09-30",
                "tourist_tax_apply_from_night": 1,
                "tourist_tax_apply_to_night": 3,
                "tourist_tax_min_age": 14,
            }
        )

        checkin = fields.Date.today()
        checkout = checkin + datetime.timedelta(days=3)

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_adult.id,
                "sale_channel_origin_id": self.sale_channel_direct.id,
                "adults": 2,
                "checkin_partner_ids": [
                    (0, 0, {"partner_id": self.partner_adult.id}),
                    (0, 0, {"partner_id": self.partner_child.id}),
                ],
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
            }
        )

        tax_services = reservation.service_ids.filtered(
            lambda s: s.product_id.product_tmpl_id.is_tourist_tax
        )
        self.assertEqual(
            len(tax_services), 1, "Should generate one tourist tax service"
        )

        service = tax_services[0]
        self.assertEqual(
            len(service.service_line_ids), 3, "Should have 3 nights of tax"
        )

        for line in service.service_line_ids:
            self.assertEqual(line.day_qty, 1, "Only adult should be taxed")
            self.assertEqual(
                line.price_unit, 2.0, "Price should match product list_price"
            )

    @freeze_time("2025-12-15")
    def test_tourist_tax_not_applied_outside_period(self):
        """
        Test that tourist tax is not applied outside the configured date range.
        """
        self.env["product.product"].create(
            {
                "name": "Tourist Tax",
                "list_price": 2.0,
                "is_tourist_tax": True,
                "per_person": True,
                "tourist_tax_date_start": "06-01",
                "tourist_tax_date_end": "09-30",
                "tourist_tax_apply_from_night": 1,
                "tourist_tax_apply_to_night": 3,
                "tourist_tax_min_age": 14,
            }
        )

        checkin = fields.Date.today()
        checkout = checkin + datetime.timedelta(days=2)

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_adult.id,
                "adults": 2,
                "sale_channel_origin_id": self.sale_channel_direct.id,
                "checkin_partner_ids": [
                    (0, 0, {"partner_id": self.partner_adult.id}),
                ],
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
            }
        )

        tax_services = reservation.service_ids.filtered(
            lambda s: s.product_id.product_tmpl_id.is_tourist_tax
        )

        self.assertEqual(
            len(tax_services),
            0,
            "No tax should be applied outside the defined MM-DD range",
        )

    @freeze_time("2025-07-01")
    def test_tourist_tax_stops_after_max_night(self):
        """
        Test that tax is not applied beyond the configured
        max night (apply_to_night = 3).
        """
        self.env["product.product"].create(
            {
                "name": "Tourist Tax",
                "list_price": 2.0,
                "is_tourist_tax": True,
                "per_person": True,
                "tourist_tax_date_start": "06-01",
                "tourist_tax_date_end": "09-30",
                "tourist_tax_apply_from_night": 1,
                "tourist_tax_apply_to_night": 3,
                "tourist_tax_min_age": 14,
            }
        )

        checkin = fields.Date.today()
        checkout = checkin + datetime.timedelta(days=5)

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_adult.id,
                "adults": 2,
                "sale_channel_origin_id": self.sale_channel_direct.id,
                "checkin_partner_ids": [
                    (0, 0, {"partner_id": self.partner_adult.id}),
                ],
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
            }
        )

        tax_services = reservation.service_ids.filtered(
            lambda s: s.product_id.product_tmpl_id.is_tourist_tax
        )

        self.assertEqual(
            len(tax_services), 1, "Should generate one tourist tax service"
        )
        service = tax_services[0]

        self.assertEqual(
            len(service.service_line_ids), 3, "Tax should only apply to first 3 nights"
        )

    @freeze_time("2025-06-28")
    def test_multiple_tourist_taxes_applied_by_season(self):
        """
        Test that two different tourist taxes
        (low and high season) apply correctly over 8 nights.
        """
        # Arrange
        low_season_tax = self.env["product.product"].create(
            {
                "name": "Tourist Tax Low Season",
                "list_price": 1.5,
                "is_tourist_tax": True,
                "per_person": True,
                "tourist_tax_date_start": "01-01",
                "tourist_tax_date_end": "06-30",
                "tourist_tax_apply_from_night": 1,
                "tourist_tax_apply_to_night": 3,
                "tourist_tax_min_age": 14,
            }
        )

        high_season_tax = self.env["product.product"].create(
            {
                "name": "Tourist Tax High Season",
                "list_price": 2.0,
                "is_tourist_tax": True,
                "per_person": True,
                "tourist_tax_date_start": "07-01",
                "tourist_tax_date_end": "09-30",
                "tourist_tax_apply_from_night": 1,
                "tourist_tax_apply_to_night": 99,
                "tourist_tax_min_age": 14,
            }
        )

        checkin = fields.Date.today()  # 2025-06-28
        checkout = checkin + datetime.timedelta(days=8)  # until 2025-07-06

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_adult.id,
                "adults": 1,
                "sale_channel_origin_id": self.sale_channel_direct.id,
                "checkin_partner_ids": [
                    (0, 0, {"partner_id": self.partner_adult.id}),
                ],
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
            }
        )

        # Act
        tax_services = reservation.service_ids.filtered(
            lambda s: s.product_id.product_tmpl_id.is_tourist_tax
        )
        # Assert
        self.assertEqual(
            len(tax_services),
            2,
            "Should generate two tourist tax services (low and high season)",
        )

        low = tax_services.filtered(lambda s: s.product_id == low_season_tax)
        high = tax_services.filtered(lambda s: s.product_id == high_season_tax)

        self.assertEqual(
            len(low.service_line_ids),
            3,
            "Low season should apply to first 3 nights (06/28–06/30)",
        )
        self.assertEqual(
            len(high.service_line_ids),
            5,
            "High season should apply to last 5 nights (07/01–07/05)",
        )

        for line in low.service_line_ids:
            self.assertEqual(line.day_qty, 1)
            self.assertEqual(line.price_unit, 1.5)

        for line in high.service_line_ids:
            self.assertEqual(line.day_qty, 1)
            self.assertEqual(line.price_unit, 2.0)
