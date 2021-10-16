import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError

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
        # make current journals payable
        journals = self.env["account.journal"].search(
            [
                ("type", "in", ["bank", "cash"]),
            ]
        )
        journals.allowed_pms_payments = True

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

    def test_reservation_type_folio(self):
        """
        Check that the reservation_type of a folio with
        a reservation with the default reservation_type is equal
        to 'normal'.
        ---------------
        A folio is created. A reservation is created to which the
        value of the folio_id is the id of the previously created
        folio. Then it is verified that the value of the reservation_type
        field of the folio is 'normal'.
        """
        # ARRANGE AND ACT
        self.partner1 = self.env["res.partner"].create({"name": "Ana"})
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner1.id,
            }
        )

        self.env["pms.reservation"].create(
            {
                "room_type_id": self.room_type_double.id,
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "folio_id": folio1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            folio1.reservation_type,
            "normal",
            "The default reservation type of the folio should be 'normal'",
        )

    def test_invoice_status_staff_reservation(self):
        """
        Check that the value of the invoice_status field is 'no'
        on a page with reservation_type equal to 'staff'.
        ------------
        A reservation is created with the reservation_type field
        equal to 'staff'. Then it is verified that the value of
        the invoice_status field of the folio created with the
        reservation is equal to 'no'.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        self.partner1 = self.env["res.partner"].create({"name": "Pedro"})
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "reservation_type": "staff",
            }
        )
        # ASSERT
        self.assertEqual(
            reservation.folio_id.invoice_status,
            "no",
            "The invoice status of the folio in a staff reservation should be 'no' ",
        )

    def test_invoice_status_out_reservation(self):
        """
        Check that the value of the invoice_status field is 'no'
        on a page with reservation_type equal to 'out'.
        ------------
        A reservation is created with the reservation_type field
        equal to 'out'. Then it is verified that the value of
        the invoice_status field of the folio created with the
        reservation is equal to 'no'.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        self.partner1 = self.env["res.partner"].create({"name": "Pedro"})
        # ACT
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "reservation_type": "out",
            }
        )
        # ASSERT
        self.assertEqual(
            reservation.folio_id.invoice_status,
            "no",
            "The invoice status of the folio in a out reservation should be 'no' ",
        )

    def test_amount_total_staff_reservation(self):
        """
        Check that the amount_total field of the folio whose
        reservation has the reservation_type field as staff
        is not calculated.
        -------------------------
        A folio is created. A reservation is created to which the
        value of the folio_id is the id of the previously created
        folio and the field reservation_type equal to 'staff'. Then
        it is verified that the value of the amount_total field of
        the folio is 0.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        self.partner1 = self.env["res.partner"].create({"name": "Pedro"})
        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner1.id,
            }
        )
        self.env["pms.reservation"].create(
            {
                "room_type_id": self.room_type_double.id,
                "checkin": checkin,
                "checkout": checkout,
                "folio_id": folio1.id,
                "reservation_type": "staff",
            }
        )
        # ASSERT
        self.assertEqual(
            folio1.amount_total,
            0.0,
            "The amount total of the folio in a staff reservation should be 0",
        )

    def test_amount_total_out_reservation(self):
        """
        Check that the amount_total field of the folio whose
        reservation has the reservation_type field as out
        is not calculated.
        -------------------------
        A folio is created. A reservation is created to which the
        value of the folio_id is the id of the previously created
        folio and the field reservation_type equal to 'out'. Then
        it is verified that the value of the amount_total field of
        the folio is 0.
        """
        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        self.partner1 = self.env["res.partner"].create({"name": "Pedro"})
        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner1.id,
            }
        )
        self.env["pms.reservation"].create(
            {
                "room_type_id": self.room_type_double.id,
                "checkin": checkin,
                "checkout": checkout,
                "folio_id": folio1.id,
                "reservation_type": "out",
            }
        )
        # ASSERT
        self.assertEqual(
            folio1.amount_total,
            0.0,
            "The amount total of the folio in a out of service reservation should be 0",
        )

    def test_reservation_type_incongruence(self):
        """
        Check that a reservation cannot be created
        with the reservation_type field different from the
        reservation_type of its folio.
        -------------
        A folio is created. A reservation is created to which the
        value of the folio_id is the id of the previously created
        folio and the field reservation_type by default('normal').
        Then it is tried to create another reservation with its
        reservation_type equal to 'staff'. But it should throw an
        error because the value of the reservation_type of the
        folio is equal to 'normal'.
        """
        self.partner1 = self.env["res.partner"].create({"name": "Ana"})
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner1.id,
            }
        )

        self.env["pms.reservation"].create(
            {
                "room_type_id": self.room_type_double.id,
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "folio_id": folio1.id,
            }
        )
        with self.assertRaises(
            ValidationError,
            msg="You cannot create reservations with different reservation_type for a folio",
        ):
            self.env["pms.reservation"].create(
                {
                    "room_type_id": self.room_type_double.id,
                    "checkin": fields.date.today(),
                    "checkout": fields.date.today() + datetime.timedelta(days=3),
                    "folio_id": folio1.id,
                    "reservation_type": "staff",
                }
            )

    def test_create_partner_in_folio(self):
        """
        Check that a res_partner is created from a folio.
        ------------
        A folio is created by adding the document_type and
        document_number fields, with these two fields a res.partner
        should be created, which is what is checked after creating
        the folio.
        """
        # ARRANGE
        self.id_category = self.env["res.partner.id_category"].create(
            {"name": "DNI", "code": "D"}
        )
        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": "Savannah Byles",
                "document_type": self.id_category.id,
                "document_number": "32861114W",
            }
        )
        # ASSERT
        self.assertTrue(folio1.partner_id.id, "The partner has not been created")

    def test_auto_complete_partner_mobile(self):
        """
        It is checked that the mobile field of the folio
        is correctly added to it when the document_number and
        document_type fields of a res.partner that exists in
        the DB are put in the folio.
        --------------------
        A res.partner is created with the name, mobile and email fields.
        The document_id is added to the res.partner. The folio is
        created and the category_id of the document_id associated with
        the res.partner is added as document_type and as document_number
        the name of the document_id associated with the res.partner as well.
        Then it is checked that the mobile of the res.partner and that of
        the folio are the same.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Enrique",
                "mobile": "654667733",
                "email": "enrique@example.com",
            }
        )
        self.id_category = self.env["res.partner.id_category"].create(
            {"name": "DNI", "code": "D"}
        )
        self.document_id = self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "61645604S",
                "partner_id": partner.id,
            }
        )
        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "document_type": self.document_id.category_id.id,
                "document_number": self.document_id.name,
            }
        )
        # ASSERT
        self.assertEqual(
            folio1.mobile,
            partner.mobile,
            "The partner mobile has not autocomplete in folio",
        )

    def test_auto_complete_partner_email(self):
        """
        It is checked that the email field of the folio
        is correctly added to it when the document_number and
        document_type fields of a res.partner that exists in
        the DB are put in the folio.
        --------------------
        A res.partner is created with the name, mobile and email fields.
        The document_id is added to the res.partner. The folio is
        created and the category_id of the document_id associated with
        the res.partner is added as document_type and as document_number
        the name of the document_id associated with the res.partner as well.
        Then it is checked that the email of the res.partner and that of
        the folio are the same.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Simon",
                "mobile": "654667733",
                "email": "simon@example.com",
            }
        )
        self.id_category = self.env["res.partner.id_category"].create(
            {"name": "DNI", "code": "D"}
        )
        self.document_id = self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "74247377L",
                "partner_id": partner.id,
            }
        )

        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "document_type": self.document_id.category_id.id,
                "document_number": self.document_id.name,
            }
        )
        # ASSERT
        self.assertEqual(
            folio1.email,
            partner.email,
            "The partner mobile has not autocomplete in folio",
        )

    def test_is_possible_customer_by_email(self):
        """
        It is checked that the field is_possible_existing_customer_id
        exists in a folio with an email from a res.partner saved
        in the DB.
        ----------------
        A res.partner is created with the name and email fields. A folio
        is created by adding the same email as the res.partner. Then it is
        checked that the field is_possible_existing_customer_id is equal to True.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Courtney Campbell",
                "email": "courtney@example.com",
            }
        )
        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "email": partner.email,
            }
        )
        # ASSERT
        self.assertTrue(
            folio1.possible_existing_customer_ids, "No customer found with this email"
        )

    def test_is_possible_customer_by_mobile(self):
        """
        It is checked that the field is_possible_existing_customer_id
        exists in a folio with a mobile from a res.partner saved
        in the DB.
        ----------------
        A res.partner is created with the name and email fields. A folio
        is created by adding the same mobile as the res.partner. Then it is
        checked that the field is_possible_existing_customer_id is equal to True.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Ledicia Sandoval",
                "mobile": "615369231",
            }
        )
        # ACT
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "mobile": partner.mobile,
            }
        )
        # ASSERT
        self.assertTrue(
            folio1.possible_existing_customer_ids,
            "No customer found with this mobile",
        )

    def test_add_possible_customer(self):
        """
        Check that a partner was correctly added to the folio
        after launching the add_partner() method of the several partners wizard
        ---------------
        A res.partner is created with name, email and mobile. A folio is created.
        The wizard is created with the folio id and the partner added to the
        possible_existing_customer_ids field. The add_partner method of the wizard
        is launched and it is checked that the partner was correctly added to the
        folio.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Serafín Rivas",
                "email": "serafin@example.com",
                "mobile": "60595595",
            }
        )

        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "email": partner.email,
            }
        )

        several_partners_wizard = self.env["pms.several.partners.wizard"].create(
            {
                "folio_id": folio1.id,
                "possible_existing_customer_ids": [(6, 0, [partner.id])],
            }
        )
        # ACT
        several_partners_wizard.add_partner()
        # ASSERT
        self.assertEqual(
            folio1.partner_id.id,
            partner.id,
            "The partner was not added to the folio ",
        )

    def test_not_add_several_possibles_customers(self):
        """
        Check that multiple partners cannot be added to a folio
        from the several partners wizard.
        ---------------
        Two res.partner are created with name, email and mobile. A folio is created.
        The wizard is created with the folio id and the two partners added to the
        possible_existing_customer_ids field. The add_partner method of the wizard
        is launched and it is verified that a Validation_Error was raised.
        """
        # ARRANGE
        partner1 = self.env["res.partner"].create(
            {
                "name": "Serafín Rivas",
                "email": "serafin@example.com",
                "mobile": "60595595",
            }
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "Simon",
                "mobile": "654667733",
                "email": "simon@example.com",
            }
        )

        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner1.name,
                "email": partner1.email,
            }
        )

        several_partners_wizard = self.env["pms.several.partners.wizard"].create(
            {
                "folio_id": folio1.id,
                "possible_existing_customer_ids": [(6, 0, [partner1.id, partner2.id])],
            }
        )

        # ACT AND ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Two partners cannot be added to the folio",
        ):
            several_partners_wizard.add_partner()

    def test_not_add_any_possibles_customers(self):
        """
        Check that the possible_existing_customer_ids field of the several
        partners wizard can be left empty and then launch the add_partner()
        method of this wizard to add a partner in folio.
        ---------------
        A folio is created. The wizard is created without the
        possible_existing_customer_ids field. The add_partner method of
        the wizard is launched and it is verified that a Validation_Error
        was raised.
        """

        # ARRANGE
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": "Rosa Costa",
            }
        )

        several_partners_wizard = self.env["pms.several.partners.wizard"].create(
            {
                "folio_id": folio1.id,
            }
        )

        # ACT AND ASSERT
        with self.assertRaises(
            ValidationError,
            msg="A partner can be added to the folio",
        ):
            several_partners_wizard.add_partner()

    def test_add_partner_invoice_contact(self):
        """
        Check that when adding a customer at check-in, reservation or folio,
        it is added as a possible billing address
        ---------------
        Three res.partner are created with name, email and mobile. A folio is created.
        We add the partners to the folio, reservation, and checkin, and check that the
        three partners are on partner_invoice in folio.
        """
        # ARRANGE
        partner1 = self.env["res.partner"].create(
            {
                "name": "Serafín Rivas",
                "email": "serafin@example.com",
                "mobile": "60595595",
            }
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "Simon",
                "mobile": "654667733",
                "email": "simon@example.com",
            }
        )
        partner3 = self.env["res.partner"].create(
            {
                "name": "Sofia",
                "mobile": "688667733",
                "email": "sofia@example.com",
            }
        )

        # FIRST ACTION
        folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner1.name,
                "email": partner1.email,
            }
        )
        reservation1 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "folio_id": folio1.id,
            }
        )

        # FIRST ASSERT
        self.assertEqual(
            len(folio1.partner_invoice_ids),
            0,
            "A partner was added as a billing contact for no reason",
        )

        # SECOND ACTION
        folio1.partner_id = partner1.id

        # SECOND ASSERT
        self.assertEqual(
            folio1.partner_invoice_ids.ids,
            [partner1.id],
            "A folio partner was not added as a billing contact",
        )

        # SECOND ACTION
        reservation1.partner_id = partner2.id

        # SECOND ASSERT
        self.assertIn(
            partner2.id,
            folio1.partner_invoice_ids.ids,
            "A reservation partner was not added as a billing contact",
        )

        # THIRD ACTION
        reservation1.checkin_partner_ids[0].partner_id = partner3.id

        # THIRD ASSERT
        self.assertIn(
            partner3.id,
            folio1.partner_invoice_ids.ids,
            "A checkin partner was not added as a billing contact",
        )
