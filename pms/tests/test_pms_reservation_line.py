import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestPms


@tagged("post_install", "-at_install")
class TestPmsReservationLines(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = cls.env["res.users"].browse(1)
        cls.env = cls.env(user=user)
        # create a room type availability
        cls.room_type_availability = cls.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [cls.pricelist1.id])],
            }
        )

        # create room type
        cls.room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
            }
        )

        cls.room_type_triple = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Triple Test",
                "default_code": "TRP_Test",
                "class_id": cls.room_type_class1.id,
            }
        )

        # Additional room type class for incompatible test
        cls.room_type_class_day = cls.env["pms.room.type.class"].create(
            {
                "name": "Day Use",
                "overnight": False,
                "default_code": "DAY",
            }
        )
        cls.room_type_class_overnight = cls.env["pms.room.type.class"].create(
            {
                "name": "Overnight",
                "overnight": True,
                "default_code": "OVN",
            }
        )

        cls.room_type_day = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Day Room",
                "default_code": "DAY_Test",
                "class_id": cls.room_type_class_day.id,
            }
        )

        cls.room_type_overnight = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Overnight Room",
                "default_code": "OVN_Test",
                "class_id": cls.room_type_class_overnight.id,
            }
        )

        cls.room_day = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Day 201",
                "room_type_id": cls.room_type_day.id,
                "capacity": 1,
                "extra_beds_allowed": 0,
            }
        )
        cls.room_overnight = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Overnight 202",
                "room_type_id": cls.room_type_overnight.id,
                "capacity": 1,
                "extra_beds_allowed": 0,
            }
        )

        # create rooms
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 101",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.room2 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 102",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.room3 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 103",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.room4 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Triple 104",
                "room_type_id": cls.room_type_triple.id,
                "capacity": 3,
                "extra_beds_allowed": 1,
            }
        )
        cls.partner1 = cls.env["res.partner"].create(
            {
                "firstname": "Jaime",
                "lastname": "García",
                "email": "jaime@example.com",
                "birthdate_date": "1983-03-01",
                "gender": "male",
            }
        )
        cls.sale_channel_direct = cls.env["pms.sale.channel"].create(
            {"name": "sale channel direct", "channel_type": "direct"}
        )
        cls.sale_channel1 = cls.env["pms.sale.channel"].create(
            {"name": "saleChannel1", "channel_type": "indirect"}
        )
        cls.agency1 = cls.env["res.partner"].create(
            {
                "firstname": "partner1",
                "is_agency": True,
                "invoice_to_agency": "always",
                "default_commission": 15,
                "sale_channel_id": cls.sale_channel1.id,
            }
        )

    @freeze_time("2000-12-01")
    def test_modify_reservation_line_with_compatible_overnight_classes(self):
        """
        Check that when modifying a reservation with compatible overnight
        classes, the reservation is modified correctly.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": self.partner1.id,
            "pms_property_id": self.pms_property1.id,
            "sale_channel_origin_id": self.sale_channel_direct.id,
        }
        reservation = self.env["pms.reservation"].create(reservation_vals)

        # ACT
        reservation.reservation_line_ids[0].write(
            {
                "room_id": self.room_overnight.id,
            }
        )

        # ASSERT
        self.assertEqual(
            reservation.reservation_line_ids[0].room_id.room_type_id.id,
            self.room_type_overnight.id,
            "The reservation should be modified with the new room type",
        )

    @freeze_time("2000-12-01")
    def test_modify_reservation_with_incompatible_overnight_classes(self):
        """
        Check that when modifying a reservation with incompatible overnight
        classes, the reservation raises an error.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation_vals = {
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.room_type_double.id,
            "partner_id": self.partner1.id,
            "pms_property_id": self.pms_property1.id,
            "sale_channel_origin_id": self.sale_channel_direct.id,
        }
        reservation = self.env["pms.reservation"].create(reservation_vals)

        # ACT & ASSERT
        with self.assertRaises(ValidationError):
            reservation.reservation_line_ids[0].write(
                {
                    "room_id": self.room_day.id,
                }
            )
