import datetime

from freezegun import freeze_time

from odoo.exceptions import ValidationError

from .common import TestPms


@freeze_time("2010-01-01")
class TestPmsSaleChannel(TestPms):
    def test_not_agency_as_agency(self):
        # ARRANGE
        PmsReservation = self.env["pms.reservation"]
        not_agency = self.env["res.partner"].create(
            {"name": "partner1", "is_agency": False}
        )

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            PmsReservation.create(
                {
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                    "agency_id": not_agency.id,
                    "pms_property_id": self.pms_property1.id,
                }
            )

    def test_channel_type_id_only_directs(self):
        # ARRANGE
        PmsReservation = self.env["pms.reservation"]
        PmsSaleChannel = self.env["pms.sale.channel"]
        # ACT
        sale_channel1 = PmsSaleChannel.create({"channel_type": "direct"})
        partner1 = self.env["res.partner"].create({"name": "partner1"})
        reservation1 = PmsReservation.create(
            {
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "channel_type_id": sale_channel1.id,
                "partner_id": partner1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation1.channel_type_id.channel_type,
            "direct",
            "Sale channel is not direct",
        )

    def test_agency_id_is_agency(self):
        # ARRANGE
        PmsReservation = self.env["pms.reservation"]
        PmsSaleChannel = self.env["pms.sale.channel"]
        sale_channel1 = PmsSaleChannel.create(
            {"name": "Test Indirect", "channel_type": "indirect"}
        )
        # ACT
        agency1 = self.env["res.partner"].create(
            {
                "name": "partner1",
                "is_agency": True,
                "sale_channel_id": sale_channel1.id,
            }
        )
        reservation1 = PmsReservation.create(
            {
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "agency_id": agency1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation1.agency_id.is_agency,
            True,
            "Agency_id doesn't correspond to an agency",
        )

    def test_sale_channel_id_only_indirect(self):
        # ARRANGE
        PmsSaleChannel = self.env["pms.sale.channel"]
        # ACT
        saleChannel1 = PmsSaleChannel.create({"channel_type": "indirect"})
        agency1 = self.env["res.partner"].create(
            {"name": "example", "is_agency": True, "sale_channel_id": saleChannel1.id}
        )
        # ASSERT
        self.assertEqual(
            agency1.sale_channel_id.channel_type,
            "indirect",
            "An agency should be a indirect channel",
        )

    def test_agency_without_sale_channel_id(self):
        # ARRANGE & ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["res.partner"].create(
                {"name": "example", "is_agency": True, "sale_channel_id": None}
            )
