import datetime

from freezegun import freeze_time

from .common import TestHotel

freeze_time("2000-02-02")


class TestPmsFolio(TestHotel):
    def test_commission_and_partner_correct(self):
        # ARRANGE
        PmsFolio = self.env["pms.folio"]
        PmsReservation = self.env["pms.reservation"]
        PmsPartner = self.env["res.partner"]
        PmsSaleChannel = self.env["pms.sale.channel"]
        # ACT
        saleChannel = PmsSaleChannel.create(
            {"name": "saleChannel1", "channel_type": "indirect"}
        )
        agency = PmsPartner.create(
            {
                "name": "partner1",
                "is_agency": True,
                "invoice_agency": True,
                "default_commission": 15,
                "sale_channel_id": saleChannel.id,
            }
        )

        reservation = PmsReservation.create(
            {
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "agency_id": agency.id,
            }
        )
        folio = PmsFolio.create(
            {
                "agency_id": agency.id,
                "reservation_ids": [reservation.id],
            }
        )

        commission = 0
        for reservation in folio.reservation_ids:
            commission += reservation.commission_amount

        # ASSERT
        self.assertEqual(
            folio.commission,
            commission,
            "Folio commission don't math with his reservation commission",
        )
        if folio.agency_id:
            self.assertEqual(
                folio.agency_id, folio.partner_id, "Agency has to be the partner"
            )
