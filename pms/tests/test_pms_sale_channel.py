from .common import TestHotel
from freezegun import freeze_time
from odoo.exceptions import ValidationError
import datetime
from odoo import fields

@freeze_time("2010-01-01")
class TestPmsSaleChannel(TestHotel):
    def test_not_agency_as_agency(self):
       #ARRANGE
       PmsReservation = self.env["pms.reservation"]
       not_agency = self.env["res.partner"].create(
           {
               "name":"partner1",
                "is_agency":False
           }
       )

       #ACT & ASSERT
       with self.assertRaises(ValidationError), self.cr.savepoint():
           PmsReservation.create(
               {
                   "checkin": datetime.datetime.now(),
                   "checkout":datetime.datetime.now() + datetime.timedelta(days=3),
                   "agency_id":not_agency.id,
               }
           )

    def test_partner_as_direct_channel(self):
        #ARRANGE
        PmsReservation = self.env["pms.reservation"]
        partner = customer = self.env.ref("base.res_partner_12")
        #ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            PmsReservation.create(
                {
                    "checkin": datetime.datetime.now(),
                    "checkout":datetime.datetime.now() + datetime.timedelta(days=3),
                    "channel_type_id":partner.id,
                }
            )

    def test_channel_type_id_only_directs(self):
        #ARRANGE
        PmsReservation = self.env["pms.reservation"]
        PmsSaleChannel = self.env["pms.sale.channel"]
        #ACT
        saleChannel = PmsSaleChannel.create(
            {
                "channel_type":"direct"
            }
        )
        reservation = PmsReservation.create(
            {
                "checkin":datetime.datetime.now(),
                "checkout":datetime.datetime.now()+datetime.datetimedelta(days=3)
                "channel_type_id": saleChannel.id
            }
        )
        #ASSERT
        self.assertEqual(
            self.browse_ref(reservation.channel_type_id).channel_type,
            "direct",
            "Sale channel is not direct"
        )

    def test_agency_id_is_agency(self):
        #ARRANGE
        PmsReservation = self.env["pms.reservation"]

        #ACT
        agency = self.env["res.partner"].create(
           {
               "name":"partner1",
                "is_agency":True
           }
       )
        reservation = PmsReservation.create(
            {
                "checkin":datetime.datetime.now(),
                "checkout":datetime.datetime.now()+datetime.datetimedelta(days=3)
                "agency_id":agency.id
            }
        )
        #ASSERT
        self.assertEqual(
            self.browse_ref(reservation.agency_id).is_agency,
            True,
            "Agency_id doesn't correspond to an agency"
        )

    def test_sale_channel_id_only_indirect(self):
        #ARRANGE
        PmsSaleChannel = self.env["pms.sale.channel"]
        #ACT
        saleChannel = PmsSaleChannel.create(
            {
                "channel_type":"indirect"
            }
        )
        agency = self.env["res.partner"].create(
            {
                "name":"example",
                "is_agency":True,
                "sale_channel_id":saleChannel.id
            }
        )
        #ASSERT
        self.assertEqual(
            self.browse_ref(agency.sale_channel_id).channel_type,
            "indirect",
            "An agency should be a indirect channel"
        )

    def test_agency_without_sale_channel_id(self):
       #ARRANGE & ACT & ASSERT
       with self.assertRaises(ValidationError), self.cr.savepoint():
           self.env["res.partner"].create(
               {
                   "name":"example",
                    "is_agency":True,
                    "sale_channel_id":None
               }
           )
