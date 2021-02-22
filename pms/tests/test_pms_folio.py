import datetime

from freezegun import freeze_time

from odoo import fields

from .common import TestHotel

freeze_time("2000-02-02")


class TestPmsFolio(TestHotel):
    def create_common_scenario(self):
        # create a room type availability
        self.room_type_availability = self.env[
            "pms.room.type.availability.plan"
        ].create({"name": "Availability plan for TEST"})

        # create a property
        self.property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        # create room type class
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "code_class": "ROOM"}
        )

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property.id],
                "name": "Double Test",
                "code_type": "DBL_Test",
                "class_id": self.room_type_class.id,
                "price": 25,
            }
        )
        # create room
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 101",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        # create room
        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 102",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

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

    def test_compute_folio_priority(self):
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )
        r1.left_for_checkin = False

        self.env["pms.reservation"].create(
            {
                "folio_id": r1.folio_id.id,
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pms_property_id": self.property.id,
            }
        )

        self.assertEqual(
            r1.priority,
            r1.folio_id.max_reservation_prior,
            "The max. reservation priority on the whole folio is incorrect",
        )

    def test_full_pay_folio(self):
        # TEST CASE
        # Folio is paid after execute
        #
        # ARRANGE
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "room_type_id": self.room_type_double.id,
            }
        )
        self.env["pms.folio"].do_payment(
            self.env["account.journal"].browse(
                r_test.folio_id.pms_property_id._get_payment_methods().ids[0]
            ),
            self.env["account.journal"]
            .browse(r_test.folio_id.pms_property_id._get_payment_methods().ids[0])
            .suspense_account_id,
            self.env.user,
            r_test.folio_id.pending_amount,
            r_test.folio_id,
            partner=r_test.partner_id,
            date=fields.date.today(),
        )
        self.assertFalse(r_test.folio_id.pending_amount)

    def test_partial_pay_folio(self):
        # TEST CASE
        # Folio is partially paid after execute
        #
        # ARRANGE
        left_to_pay = 1
        self.create_common_scenario()
        r_test = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "room_type_id": self.room_type_double.id,
            }
        )
        self.env["pms.folio"].do_payment(
            self.env["account.journal"].browse(
                r_test.folio_id.pms_property_id._get_payment_methods().ids[0]
            ),
            self.env["account.journal"]
            .browse(r_test.folio_id.pms_property_id._get_payment_methods().ids[0])
            .suspense_account_id,
            self.env.user,
            r_test.folio_id.pending_amount - left_to_pay,
            r_test.folio_id,
            partner=r_test.partner_id,
            date=fields.date.today(),
        )
        self.assertEqual(r_test.folio_id.pending_amount, left_to_pay)
