import datetime

from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsSaleChannel(TestPms):
    def test_reservation_with_invalid_agency(self):
        """
        Reservation with an invalid agency cannot be created.
        Create a partner that is not an agency and create
        a reservation with that partner as an agency.
        """
        # ARRANGE
        PmsReservation = self.env["pms.reservation"]
        not_agency = self.env["res.partner"].create(
            {"name": "partner1", "is_agency": False}
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Reservation with an invalid agency cannot be created."
        ):
            PmsReservation.create(
                {
                    "checkin": datetime.datetime.now(),
                    "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                    "agency_id": not_agency.id,
                    "pms_property_id": self.pms_property1.id,
                }
            )

    def test_reservation_with_valid_agency(self):
        """
        Reservation with a valid agency must be created.
        Create a partner that is an agency and create
        a reservation with that partner as an agency can be created.
        """
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
            "Reservation with a valid agency should be created.",
        )

    def test_reservation_with_partner_direct(self):
        """
        Reservation create with partner (no agency) and sale channel
        'direct' must be set reservation sale channel to 'direct'.
        A reservation with partner and sale channel as 'direct'
        should be created.
        """
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
            "A reservation with partner and sale channel as 'direct'"
            "should be created a 'direct' reservation.",
        )

    def test_reservation_with_partner_indirect(self):
        """
        Reservation create with partner (no agency) and sale channel
        'indirect' must be set reservation sale channel to 'direct'.
        A reservation with partner and sale channel as 'direct'
        should be created.
        """
        # ARRANGE
        PmsReservation = self.env["pms.reservation"]
        PmsSaleChannel = self.env["pms.sale.channel"]
        # ACT
        sale_channel1 = PmsSaleChannel.create({"channel_type": "indirect"})
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
            "indirect",
            "A reservation with partner and sale channel as 'direct'"
            "should be created a 'indirect' reservation.",
        )

    def test_create_agency_with_sale_channel_indirect(self):
        """
        Agency should be created as partner setted as 'agency'
        and its sale channel as 'indirect'.
        """
        # ARRANGE
        PmsSaleChannel = self.env["pms.sale.channel"]
        saleChannel1 = PmsSaleChannel.create({"channel_type": "indirect"})
        # ACT
        agency1 = self.env["res.partner"].create(
            {"name": "example", "is_agency": True, "sale_channel_id": saleChannel1.id}
        )
        # ASSERT
        self.assertEqual(
            agency1.sale_channel_id.channel_type,
            "indirect",
            "An agency should be an indirect channel.",
        )

    def test_create_agency_with_sale_channel_direct(self):
        """
        Agency shouldnt be created as partner setted as 'agency'
        and its sale channel as 'direct'.
        """
        # ARRANGE
        PmsSaleChannel = self.env["pms.sale.channel"]
        saleChannel1 = PmsSaleChannel.create({"channel_type": "direct"})
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="An agency should be an indirect channel."
        ):
            self.env["res.partner"].create(
                {
                    "name": "example",
                    "is_agency": True,
                    "sale_channel_id": saleChannel1.id,
                }
            )

    def test_create_agency_without_sale_channel(self):
        """
        Agency creation should fails if there's no sale channel.
        """
        # ARRANGE & ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Agency should not be created without sale channel."
        ):
            self.env["res.partner"].create(
                {"name": "example", "is_agency": True, "sale_channel_id": None}
            )
