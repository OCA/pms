from freezegun import freeze_time

from .common import TestHotel


@freeze_time("2012-01-14")
class TestPmsCheckinPartner(TestHotel):
    @classmethod
    def setUpClass(cls):
        super(TestHotel, cls).setUpClass()

    def test_create_checkin_partner(self):

        # ARRANGE
        host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        reservation_vals = {
            "checkin": "2012-01-14",
            "checkout": "2012-01-17",
            "room_type_id": self.env.ref("pms.pms_room_type_3").id,
            "partner_id": host1.id,
            "pms_property_id": self.env.ref("pms.main_pms_property").id,
        }
        demo_user = self.env.ref("base.user_demo")

        # ACT
        reservation_1 = (
            self.env["pms.reservation"].with_user(demo_user).create(reservation_vals)
        )
        checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": host1.id,
                "reservation_id": reservation_1.id,
            }
        )
        checkin1.onboard()

        # ASSERT
        self.assertEqual(
            checkin1.state,
            "onboard",
            "the checkin was not successful",
        )
