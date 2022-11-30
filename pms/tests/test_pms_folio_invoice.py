import datetime

from odoo import fields

from .common import TestPms


class TestPmsFolioInvoice(TestPms):
    def setUp(self):
        super().setUp()
        # create a room type availability
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {"name": "Availability plan for TEST"}
        )

        # journal to simplified invoices
        self.simplified_journal = self.env["account.journal"].create(
            {
                "name": "Simplified journal",
                "code": "SMP",
                "type": "sale",
                "company_id": self.env.ref("base.main_company").id,
            }
        )

        # create a property
        self.property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.pricelist1.id,
                "journal_simplified_invoice_id": self.simplified_journal.id,
            }
        )

        # create room type
        self.room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )

        # create rooms
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 101",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 102",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        self.room3 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property.id,
                "name": "Double 103",
                "room_type_id": self.room_type_double.id,
                "capacity": 2,
            }
        )

        # res.partner
        self.partner_id = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "vat": "45224522J",
                "country_id": self.env.ref("base.es").id,
                "city": "Madrid",
                "zip": "28013",
                "street": "Calle de la calle",
            }
        )

        # create a sale channel
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
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
        # make current journals payable
        journals = self.env["account.journal"].search(
            [
                ("type", "in", ["bank", "cash"]),
            ]
        )
        journals.allowed_pms_payments = True

    def test_invoice_full_folio(self):
        """
        Check that when launching the create_invoices() method for a full folio,
        the invoice_status field is set to "invoiced".
        ----------------
        A reservation is created. The create_invoices() method of the folio of
        that reservation is launched. It is verified that the invoice_status field
        of the folio is equal to "invoiced".
        """
        # ARRANGE
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        state_expected = "invoiced"
        # ACT
        r1.folio_id._create_invoices()
        # ASSERT
        self.assertEqual(
            state_expected,
            r1.folio_id.invoice_status,
            "The status after a full invoice folio isn't correct",
        )

    def test_invoice_partial_folio_by_steps(self):
        """
        Check that when launching the create_invoices() method for a partial folio,
        the invoice_status field is set to "invoiced".
        ----------------
        A reservation is created. The create_invoices() method of the folio of
        that reservation is launched with the first sale line. It is verified
        that the invoice_status field of the folio is equal to "invoiced".
        """
        # ARRANGE
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        dict_lines = dict()

        dict_lines[
            r1.folio_id.sale_line_ids.filtered(lambda l: not l.display_type)[0].id
        ] = 3
        r1.folio_id._create_invoices(lines_to_invoice=dict_lines)

        self.assertEqual(
            "invoiced",
            r1.folio_id.invoice_status,
            "The status after an invoicing is not correct",
        )

    def test_invoice_partial_folio_diferent_partners(self):
        # ARRANGE
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        dict_lines = dict()
        # qty to 1 to 1st folio sale line
        dict_lines[
            r1.folio_id.sale_line_ids.filtered(lambda l: not l.display_type)[0].id
        ] = 1
        r1.folio_id._create_invoices(
            lines_to_invoice=dict_lines,
            partner_invoice_id=self.env.ref("base.res_partner_1").id,
        )

        # test does not work without invalidating cache
        self.env["account.move"].invalidate_cache()

        self.assertNotEqual(
            "invoiced",
            r1.folio_id.invoice_status,
            "The status after a partial invoicing is not correct",
        )
        # qty to 2 to 1st folio sale line
        dict_lines[
            r1.folio_id.sale_line_ids.filtered(lambda l: not l.display_type)[0].id
        ] = 2
        r1.folio_id._create_invoices(
            lines_to_invoice=dict_lines,
            partner_invoice_id=self.env.ref("base.res_partner_12").id,
        )
        self.assertNotEqual(
            r1.folio_id.move_ids.mapped("partner_id")[0],
            r1.folio_id.move_ids.mapped("partner_id")[1],
            "The status after an invoicing is not correct",
        )

    def test_amount_invoice_folio(self):
        """
        Test create and invoice from the Folio, and check amount of the reservation.
        -------------
        A reservation is created. The create_invoices() method is launched and it is
        verified that the total amount of the reservation folio is equal to the total
        of the created invoice.
        """
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        total_amount_expected = r1.folio_id.amount_total
        r1.folio_id._create_invoices()
        self.assertEqual(
            r1.folio_id.move_ids.amount_total,
            total_amount_expected,
            "Total amount of the invoice and total amount of folio don't match",
        )

    def test_qty_to_invoice_folio(self):
        """
        Test create and invoice from the Folio, and check qty to invoice.
        ----------------------
        A reservation is created.Then it is verified that the total quantity
        to be invoice from the sale lines of the reservation folio corresponds
        to expected.
        """
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        qty_to_invoice_expected = sum(
            r1.folio_id.sale_line_ids.mapped("qty_to_invoice")
        )
        self.assertEqual(
            qty_to_invoice_expected,
            3.0,
            "The quantity to be invoice on the folio does not correspond",
        )

    def test_qty_invoiced_folio(self):
        """
        Test create and invoice from the Folio, and check qty invoiced.
        ---------------
        A reservation is created.The create_invoices() method is launched and it is
        verified that the total quantity invoiced of the reservation folio is equal
        to the total quantity of the created invoice.
        """
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        r1.folio_id._create_invoices()
        qty_invoiced_expected = sum(r1.folio_id.sale_line_ids.mapped("qty_invoiced"))
        self.assertEqual(
            qty_invoiced_expected,
            3.0,
            "The quantity invoiced on the folio does not correspond",
        )

    def test_price_invoice_by_services_folio(self):
        """
        Test create and invoice from the Folio, and check amount in a
        specific segment of services.
        """

        self.product1 = self.env["product.product"].create(
            {"name": "Test Product 1", "per_day": True, "list_price": 10}
        )

        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product1.id,
                "reservation_id": self.reservation1.id,
            }
        )

        dict_lines = dict()
        dict_lines[
            self.reservation1.folio_id.sale_line_ids.filtered("service_id")[0].id
        ] = 3
        self.reservation1.folio_id._create_invoices(lines_to_invoice=dict_lines)
        self.assertEqual(
            self.reservation1.folio_id.sale_line_ids.filtered("service_id")[
                0
            ].price_total,
            self.reservation1.folio_id.move_ids.amount_total,
            "The service price don't match between folio and invoice",
        )

    def test_qty_invoiced_by_services_folio(self):
        """
        Test create and invoice from the Folio, and check qty invoiced
        in a specific segment of services
        """

        self.product1 = self.env["product.product"].create(
            {"name": "Test Product 1", "per_day": True, "list_price": 10}
        )

        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product1.id,
                "reservation_id": self.reservation1.id,
            }
        )

        dict_lines = dict()
        service_lines = self.reservation1.folio_id.sale_line_ids.filtered("service_id")
        for line in service_lines:
            dict_lines[line.id] = 1
            self.reservation1.folio_id._create_invoices(lines_to_invoice=dict_lines)
        expected_qty_invoiced = sum(
            self.reservation1.folio_id.move_ids.invoice_line_ids.mapped("quantity")
        )
        self.assertEqual(
            expected_qty_invoiced,
            sum(self.reservation1.folio_id.sale_line_ids.mapped("qty_invoiced")),
            "The quantity of invoiced services don't match between folio and invoice",
        )

    def test_qty_to_invoice_by_services_folio(self):
        """
        Test create an invoice from the Folio, and check qty to invoice
        in a specific segment of services
        """

        self.product1 = self.env["product.product"].create(
            {"name": "Test Product 1", "per_day": True, "list_price": 10}
        )

        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product1.id,
                "reservation_id": self.reservation1.id,
            }
        )

        expected_qty_to_invoice = sum(
            self.reservation1.folio_id.sale_line_ids.filtered("service_id").mapped(
                "qty_to_invoice"
            )
        )
        self.assertEqual(
            expected_qty_to_invoice,
            3.0,
            "The quantity of services to be invoice is wrong",
        )

    def test_price_invoice_board_service(self):
        """
        Test create and invoice from the Folio, and check the related
        amounts with board service linked
        """
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
            }
        )
        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        dict_lines = dict()
        dict_lines[
            self.reservation1.folio_id.sale_line_ids.filtered("service_id")[0].id
        ] = 1
        self.reservation1.folio_id._create_invoices(lines_to_invoice=dict_lines)
        self.assertEqual(
            self.reservation1.folio_id.sale_line_ids.filtered("service_id")[
                0
            ].price_total,
            self.reservation1.folio_id.move_ids.amount_total,
            "The board service price don't match between folio and invoice",
        )

    def test_qty_invoiced_board_service(self):
        """
        Test create and invoice from the Folio, and check qty invoiced
        with board service linked.
        """
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
            }
        )
        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        dict_lines = dict()
        service_lines = self.reservation1.folio_id.sale_line_ids.filtered("service_id")
        for line in service_lines:
            dict_lines[line.id] = 1
            self.reservation1.folio_id._create_invoices(lines_to_invoice=dict_lines)
        expected_qty_invoiced = sum(
            self.reservation1.folio_id.move_ids.invoice_line_ids.mapped("quantity")
        )
        self.assertEqual(
            expected_qty_invoiced,
            sum(self.reservation1.folio_id.sale_line_ids.mapped("qty_invoiced")),
            "The quantity of invoiced board services don't match between folio and invoice",
        )

    def test_qty_to_invoice_board_service(self):
        """
        Test create and invoice from the Folio, and check qty to invoice
        with board service linked
        """
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
            }
        )
        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        dict_lines = dict()
        service_lines = self.reservation1.folio_id.sale_line_ids.filtered("service_id")
        for line in service_lines:
            dict_lines[line.id] = 1
            self.reservation1.folio_id._create_invoices(lines_to_invoice=dict_lines)
        expected_qty_to_invoice = sum(
            self.reservation1.folio_id.sale_line_ids.filtered("service_id").mapped(
                "qty_to_invoice"
            )
        )
        self.assertEqual(
            expected_qty_to_invoice,
            0,
            "The quantity of board services to be invoice is wrong",
        )

    def test_autoinvoice_folio_checkout_property_policy(self):
        """
        Test create and invoice the cron by property preconfig automation
        --------------------------------------
        Set property default_invoicing_policy to checkout with 0 days with
        margin, and check that the folio autoinvoice date is set to last checkout
        folio date
        """
        # ARRANGE
        self.property.default_invoicing_policy = "checkout"
        self.property.margin_days_autoinvoice = 0

        # ACT
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        # ASSERT
        self.assertIn(
            datetime.date.today() + datetime.timedelta(days=3),
            self.reservation1.folio_id.mapped("sale_line_ids.autoinvoice_date"),
            "The autoinvoice date in folio with property checkout policy is wrong",
        )

    def test_autoinvoice_folio_checkout_partner_policy(self):
        """
        Test create and invoice the cron by partner preconfig automation
        --------------------------------------
        Set partner invoicing_policy to checkout with 2 days with
        margin, and check that the folio autoinvoice date is set to last checkout
        folio date + 2 days
        """
        # ARRANGE
        self.partner_id.invoicing_policy = "checkout"
        self.partner_id.margin_days_autoinvoice = 2

        # ACT
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.reservation1.reservation_line_ids.default_invoice_to = self.partner_id

        # ASSERT
        self.assertEqual(
            datetime.date.today() + datetime.timedelta(days=5),
            self.reservation1.folio_id.sale_line_ids.filtered(
                lambda l: l.invoice_status == "to_invoice"
            )[0].autoinvoice_date,
            "The autoinvoice date in folio with property checkout policy is wrong",
        )

    def test_autoinvoice_paid_folio_overnights_partner_policy(self):
        """
        Test create and invoice the cron by partner preconfig automation
        with partner setted as default invoiced to in reservation lines
        --------------------------------------
        Set partner invoicing_policy to checkout, create a reservation
        with room, board service and normal service, run autoinvoicing
        method and check that only room and board service was invoiced
        in partner1, the folio must be paid

        """
        # ARRANGE
        self.create_configuration_accounting_scenario()
        self.partner_id2 = self.env["res.partner"].create(
            {
                "name": "Sara",
                "vat": "54235544A",
                "country_id": self.env.ref("base.es").id,
                "city": "Madrid",
                "zip": "28013",
                "street": "Street 321",
            }
        )
        self.partner_id.invoicing_policy = "checkout"
        self.partner_id.margin_days_autoinvoice = 0
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.product2 = self.env["product.product"].create(
            {
                "name": "Test Product 2",
                "lst_price": 100,
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
                "amount": 10,
            }
        )

        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.demo_room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )
        # ACT
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property_demo.id,
                "checkin": datetime.date.today() - datetime.timedelta(days=3),
                "checkout": datetime.date.today(),
                "adults": 2,
                "room_type_id": self.demo_room_type_double.id,
                "partner_id": self.partner_id2.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product2.id,
                "reservation_id": self.reservation1.id,
            }
        )
        folio = self.reservation1.folio_id
        reservation1 = self.reservation1
        reservation1.reservation_line_ids.default_invoice_to = self.partner_id
        reservation1.service_ids.filtered(
            "is_board_service"
        ).default_invoice_to = self.partner_id

        folio.do_payment(
            journal=self.env["account.journal"].browse(
                reservation1.folio_id.pms_property_id._get_payment_methods().ids[0]
            ),
            receivable_account=self.env["account.journal"]
            .browse(reservation1.folio_id.pms_property_id._get_payment_methods().ids[0])
            .suspense_account_id,
            user=self.env.user,
            amount=reservation1.folio_id.pending_amount,
            folio=folio,
            partner=reservation1.partner_id,
            date=fields.date.today(),
        )
        self.pms_property_demo.autoinvoicing()

        # ASSERT
        overnight_sale_lines = self.reservation1.folio_id.sale_line_ids.filtered(
            lambda line: line.reservation_line_ids or line.is_board_service
        )
        partner_invoice = self.reservation1.folio_id.move_ids.filtered(
            lambda inv: inv.partner_id == self.partner_id
        )
        self.assertEqual(
            partner_invoice.mapped("line_ids.folio_line_ids.id"),
            overnight_sale_lines.ids,
            "Billed services and overnights invoicing wrong compute",
        )

    def test_not_autoinvoice_unpaid_cancel_folio_partner_policy(self):
        """
        Test create and invoice the cron by partner preconfig automation
        --------------------------------------
        Set partner invoicing_policy to checkout, create a reservation
        with room, board service and normal service, run autoinvoicing
        method and check that not invoice was created becouse
        the folio is cancel and not paid
        """
        # ARRANGE
        self.partner_id.invoicing_policy = "checkout"
        self.partner_id.margin_days_autoinvoice = 0
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.product2 = self.env["product.product"].create(
            {
                "name": "Test Product 2",
                "lst_price": 100,
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
                "amount": 10,
            }
        )

        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )
        # ACT
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.date.today() - datetime.timedelta(days=3),
                "checkout": datetime.date.today(),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": self.product2.id,
                "reservation_id": self.reservation1.id,
            }
        )
        self.reservation1.action_cancel()
        self.property.autoinvoicing()

        # ASSERT
        partner_invoice = self.reservation1.folio_id.move_ids.filtered(
            lambda inv: inv.partner_id == self.partner_id
        )
        self.assertEqual(
            partner_invoice.mapped("line_ids.folio_line_ids.id"),
            [],
            "Billed services and overnights invoicing wrong compute",
        )

    def _test_invoice_line_group_by_room_type_sections(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the grouped invoice lines by room type, by one
        line by unit prices/qty with nights"""

    def _test_downpayment(self):
        """Test invoice qith a way of downpaument and check dowpayment's
        folio line is created and also check a total amount of invoice is
        equal to a respective folio's total amount"""

    def _test_invoice_with_discount(self):
        """Test create with a discount and check discount applied
        on both Folio lines and an inovoice lines"""

    def _test_reinvoice(self):
        """Test the compute reinvoice folio take into account
        nights and services qty invoiced"""
