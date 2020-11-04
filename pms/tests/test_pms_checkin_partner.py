import logging

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestHotel

_logger = logging.getLogger(__name__)


@freeze_time("2012-01-14")
class TestPmsCheckinPartner(TestHotel):
    @classmethod
    def arrange_single_checkin(cls):
        # Arrange for one checkin on one reservation
        cls.host1 = cls.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        reservation_vals = {
            "checkin": "2012-01-14",
            "checkout": "2012-01-17",
            "room_type_id": cls.env.ref("pms.pms_room_type_3").id,
            "partner_id": cls.host1.id,
            "pms_property_id": cls.env.ref("pms.main_pms_property").id,
        }
        demo_user = cls.env.ref("base.user_demo")
        cls.reservation_1 = (
            cls.env["pms.reservation"].with_user(demo_user).create(reservation_vals)
        )
        cls.checkin1 = cls.env["pms.checkin.partner"].create(
            {
                "partner_id": cls.host1.id,
                "reservation_id": cls.reservation_1.id,
            }
        )

    def test_onboard_checkin(self):

        # ARRANGE
        self.arrange_single_checkin()

        # ACT
        self.checkin1.action_on_board()

        # ASSERT
        self.assertEqual(
            self.checkin1.state,
            "onboard",
            "the partner checkin was not successful",
        )

    def test_onboard_reservation(self):

        # ARRANGE
        self.arrange_single_checkin()

        # ACT
        self.checkin1.action_on_board()

        # ASSERT
        self.assertEqual(
            self.reservation_1.state,
            "onboard",
            "the reservation checkin was not successful",
        )

    def test_premature_checkin(self):
        # ARRANGE
        self.arrange_single_checkin()
        self.reservation_1.write(
            {
                "checkin": "2012-01-15",
            }
        )

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.checkin1.action_on_board()

    def test_late_checkin(self):
        # ARRANGE
        self.arrange_single_checkin()
        self.reservation_1.write(
            {
                "checkin": "2012-01-13",
            }
        )

        # ACT
        self.checkin1.action_on_board()

        # ASSERT
        self.assertEqual(
            self.checkin1.arrival,
            fields.datetime.now(),
            "the late checkin has problems",
        )

    def test_too_many_people_checkin(self):
        # ARRANGE
        self.arrange_single_checkin()
        host2 = self.env["res.partner"].create(
            {
                "name": "Carlos",
                "phone": "654667733",
                "email": "carlos@example.com",
            }
        )
        host3 = self.env["res.partner"].create(
            {
                "name": "Enmanuel",
                "phone": "654667733",
                "email": "enmanuel@example.com",
            }
        )
        host4 = self.env["res.partner"].create(
            {
                "name": "Enrique",
                "phone": "654667733",
                "email": "enrique@example.com",
            }
        )
        self.env["pms.checkin.partner"].create(
            {
                "partner_id": host2.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        self.env["pms.checkin.partner"].create(
            {
                "partner_id": host3.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["pms.checkin.partner"].create(
                {
                    "partner_id": host4.id,
                    "reservation_id": self.reservation_1.id,
                }
            )
