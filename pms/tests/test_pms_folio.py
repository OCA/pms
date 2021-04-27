import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common

freeze_time("2000-02-02")


class TestPmsFolio(common.SavepointCase):
    def create_common_scenario(self):
        # create a room type availability
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {"name": "Availability plan for TEST"}
        )
        # sequences
        self.folio_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.reservation_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.checkin_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        # create a property
        self.property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        # create room type class
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "default_code": "ROOM"}
        )

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
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

    def create_multiproperty_scenario(self):
        self.create_common_scenario()
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Property_1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

    def test_commission_and_partner_correct(self):
        # ARRANGE
        self.create_common_scenario()
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
                "invoice_to_agency": True,
                "default_commission": 15,
                "sale_channel_id": saleChannel.id,
            }
        )

        folio = PmsFolio.create(
            {
                "agency_id": agency.id,
                "pms_property_id": self.property.id,
            }
        )

        reservation = PmsReservation.create(
            {
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "agency_id": agency.id,
                "folio_id": folio.id,
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
        r1.allowed_checkin = False

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

    def test_closure_reason_property(self):
        self.create_multiproperty_scenario()
        cl_reason = self.env["room.closure.reason"].create(
            {
                "name": "closure_reason_test",
                "pms_property_ids": [
                    (4, self.property1.id),
                    (4, self.property2.id),
                ],
            }
        )

        with self.assertRaises(UserError):
            self.env["pms.folio"].create(
                {
                    "pms_property_id": self.property3.id,
                    "closure_reason_id": cl_reason.id,
                }
            )

    def _test_compute_currency(self):
        self.create_common_scenario()
        self.currency1 = self.env["res.currency"].create(
            {
                "name": "currency1",
                "symbol": "C",
            }
        )
        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "pricelist 1",
                "pms_property_ids": [
                    (4, self.property.id),
                ],
                "currency_id": self.currency1.id,
            }
        )
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "partner_id": self.env.ref("base.res_partner_12").id,
                "pricelist_id": self.pricelist.id,
            }
        )
        self.assertEqual(
            self.currency1.id,
            self.reservation1.folio_id.currency_id.id,
            "Currency must match",
        )
