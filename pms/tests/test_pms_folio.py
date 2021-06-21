import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError

from .common import TestPms


class TestPmsFolio(TestPms):

    # SetUp and Common Scenarios methods

    def setUp(self):
        """
        - common + room_type_double with 2 rooms (double1 and double2) in pms_property1
        """
        super().setUp()

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        # create room
        self.double1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 101",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        # create room
        self.double2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 102",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

    def create_multiproperty_scenario(self):
        """
        Just 2 properties to majors
        """
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        self.pms_property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

    def create_sale_channel_scenario(self):
        """
        Method to simplified scenario on sale channel tests:
        - create a sale_channel1 like indirect
        - create a agency1 like sale_channel1 agency
        """
        PmsPartner = self.env["res.partner"]
        PmsSaleChannel = self.env["pms.sale.channel"]

        self.sale_channel1 = PmsSaleChannel.create(
            {"name": "saleChannel1", "channel_type": "indirect"}
        )
        self.agency1 = PmsPartner.create(
            {
                "name": "partner1",
                "is_agency": True,
                "invoice_to_agency": True,
                "default_commission": 15,
                "sale_channel_id": self.sale_channel1.id,
            }
        )

    def create_configuration_accounting_scenario(self):
        """
        Method to simplified scenario to payments and accounting:
        # REVIEW:
        - Use new property with odoo demo data company to avoid account configuration
        - Emule SetUp with new property:
            - create demo_room_type_double
            - Create 2 rooms room_type_double
        """
        self.pms_property_demo = self.env["pms.property"].create(
            {
                "name": "Property Based on Comapany Demo",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )
        # create room type
        self.demo_room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property_demo.id],
                "name": "Double Test",
                "default_code": "Demo_DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        # create rooms
        self.double1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property_demo.id,
                "name": "Double 101",
                "room_type_id": self.demo_room_type_double.id,
                "capacity": 2,
            }
        )
        self.double2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property_demo.id,
                "name": "Double 102",
                "room_type_id": self.demo_room_type_double.id,
                "capacity": 2,
            }
        )

    # TestCases: Sale Channels

    def test_default_agency_commission(self):
        """
        Check the total commission of a folio with agency based on the
        reservation night price and the preconfigured commission in the agency.
        -------
        Agency with 15% default commision, folio with one reservation
        and 3 nights at 20$ by night (60$ total)
        """
        # ARRANGE
        self.create_sale_channel_scenario()
        commission = (20 + 20 + 20) * 0.15

        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "agency_id": self.agency1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        self.env["pms.reservation"].create(
            {
                "folio_id": folio1.id,
                "room_type_id": self.room_type_double.id,
                "reservation_line_ids": [
                    (
                        0,
                        False,
                        {
                            "date": fields.date.today(),
                            "price": 20,
                        },
                    ),
                    (
                        0,
                        False,
                        {
                            "date": fields.date.today() + datetime.timedelta(days=1),
                            "price": 20,
                        },
                    ),
                    (
                        0,
                        False,
                        {
                            "date": fields.date.today() + datetime.timedelta(days=2),
                            "price": 20,
                        },
                    ),
                ],
            }
        )
        # ASSERT
        self.assertEqual(
            commission, folio1.commission, "The folio compute commission is wrong"
        )

    def test_reservation_agency_without_partner(self):
        """
        Check that a reservation / folio created with an agency
        and without a partner will automatically take the partner.
        -------
        Create the folio1 and the reservation1, only set agency_id,
        and the partner_id should be the agency itself.
        """
        # ARRANGE
        self.create_sale_channel_scenario()

        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "agency_id": self.agency1.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        reservation1 = self.env["pms.reservation"].create(
            {
                "room_type_id": self.room_type_double.id,
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "folio_id": folio1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            reservation1.agency_id, folio1.partner_id, "Agency has to be the partner"
        )

    # TestCases: Priority

    def test_compute_folio_priority(self):
        """
        Check the priority of a folio based on its reservations
        #TODO: Commented test waiting to redefine the priority calculation
        """
        # reservation1 = self.env["pms.reservation"].create(
        #     {
        #         "checkin": fields.date.today(),
        #         "checkout": fields.date.today() + datetime.timedelta(days=1),
        #         "room_type_id": self.room_type_double.id,
        #         "partner_id": self.env.ref("base.res_partner_12").id,
        #         "pms_property_id": self.property.id,
        #     }
        # )
        # reservation1.allowed_checkin = False

        # self.env["pms.reservation"].create(
        #     {
        #         "folio_id": reservation1.folio_id.id,
        #         "checkin": fields.date.today(),
        #         "checkout": fields.date.today() + datetime.timedelta(days=1),
        #         "room_type_id": self.room_type_double.id,
        #         "partner_id": self.env.ref("base.res_partner_12").id,
        #         "pms_property_id": self.property.id,
        #     }
        # )

        # self.assertEqual(
        #     reservation1.priority,
        #     reservation1.folio_id.max_reservation_priority,
        #     "The max. reservation priority on the whole folio is incorrect",
        # )

    # TestCases: Payments
    @freeze_time("2000-02-02")
    def test_full_pay_folio(self):
        """
        After making the payment of a folio for the entire amount,
        check that there is nothing pending.
        -----
        We create a reservation (autocalculates the amounts) and
        then make the payment using the do_payment method of the folio,
        directly indicating the pending amount on the folio of the newly
        created reservation
        """
        # ARRANGE
        self.create_configuration_accounting_scenario()
        reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property_demo.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "room_type_id": self.demo_room_type_double.id,
            }
        )

        # ACTION
        self.env["pms.folio"].do_payment(
            journal=self.env["account.journal"].browse(
                reservation1.folio_id.pms_property_id._get_payment_methods().ids[0]
            ),
            receivable_account=self.env["account.journal"]
            .browse(reservation1.folio_id.pms_property_id._get_payment_methods().ids[0])
            .suspense_account_id,
            user=self.env.user,
            amount=reservation1.folio_id.pending_amount,
            folio=reservation1.folio_id,
            partner=reservation1.partner_id,
            date=fields.date.today(),
        )

        # ASSERT
        self.assertFalse(
            reservation1.folio_id.pending_amount,
            "The pending amount of a folio paid in full has not been zero",
        )

    @freeze_time("2000-02-02")
    def test_partial_pay_folio(self):
        """
        After making the payment of a folio for the partial amount,
        We check that the pending amount is the one that corresponds to it.
        -----
        We create a reservation (autocalculates the amounts) and
        then make the payment using the do_payment method of the folio,
        directly indicating the pending amount on the folio MINUS 1$
        of the newly created reservation
        """
        # ARRANGE
        self.create_configuration_accounting_scenario()
        left_to_pay = 1
        reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property_demo.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "partner_id": self.env.ref("base.res_partner_12").id,
                "room_type_id": self.demo_room_type_double.id,
            }
        )

        # ACTION
        self.env["pms.folio"].do_payment(
            journal=self.env["account.journal"].browse(
                reservation1.folio_id.pms_property_id._get_payment_methods().ids[0]
            ),
            receivable_account=self.env["account.journal"]
            .browse(reservation1.folio_id.pms_property_id._get_payment_methods().ids[0])
            .suspense_account_id,
            user=self.env.user,
            amount=reservation1.folio_id.pending_amount - left_to_pay,
            folio=reservation1.folio_id,
            partner=reservation1.partner_id,
            date=fields.date.today(),
        )

        # ASSERT
        self.assertEqual(
            reservation1.folio_id.pending_amount,
            left_to_pay,
            "The pending amount on a partially paid folio it \
            does not correspond to the amount that it should",
        )

    # TestCases: Property Consistencies

    def test_folio_closure_reason_consistency_properties(self):
        """
        Check the multioproperty consistencia between
        clousure reasons and folios
        -------
        create multiproperty scenario (3 properties in total) and
        a new clousure reason in pms_property1 and pms_property2, then, create
        a new folio in property3 and try to set the clousure_reason
        waiting a error property consistency.
        """
        # ARRANGE
        self.create_multiproperty_scenario()
        cl_reason = self.env["room.closure.reason"].create(
            {
                "name": "closure_reason_test",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
            }
        )

        # ACTION & ASSERT
        with self.assertRaises(
            UserError,
            msg="Folio created with clousure_reason_id with properties inconsistence",
        ):
            self.env["pms.folio"].create(
                {
                    "pms_property_id": self.pms_property3.id,
                    "closure_reason_id": cl_reason.id,
                }
            )
