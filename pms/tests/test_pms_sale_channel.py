from .common import TestHotel
from freezegun import freeze_time
from odoo.exceptions import ValidationError
import datetime
from odoo import fields

@freeze_time("2010-01-01")
class TestPmsSaleChannel(TestHotel):
    def test_reservation_indirect_channel(self):
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
                   "channel_type":"indirect",
                   "partner_id":not_agency.id,
               }
           )

    def test_reservation_direct_channel(self):
        PmsReservation = self.env["pms.reservation"]
        agency = self.env["res.partner"].create(
            {
                "name":"partner2",
                "is_agency":True,
            }
        )
        #ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            PmsReservation.create(
                    {
                    "checkin": datetime.datetime.now() +datetime.timedelta(days=5),
                    "checkout":datetime.datetime.now() + datetime.timedelta(days=8),
                    "channel_type":"direct",
                    "partner_id":agency.id,
                }
            )








