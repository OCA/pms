import datetime

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from .common import TestPms


@tagged("post_install", "-at_install")
class TestPmsFolioInvoice(TestPms, AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = cls.env["res.users"].browse(1)
        cls.env = cls.env(user=user)
        # create a room type availability
        cls.room_type_availability = cls.env["pms.availability.plan"].create(
            {"name": "Availability plan for TEST"}
        )

        # journal to simplified invoices
        cls.simplified_journal = cls.env["account.journal"].create(
            {
                "name": "Simplified journal",
                "code": "SMP",
                "type": "sale",
                "company_id": cls.env.ref("base.main_company").id,
            }
        )

        # create a property
        cls.property = cls.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": cls.env.ref("base.main_company").id,
                "default_pricelist_id": cls.pricelist1.id,
                "journal_simplified_invoice_id": cls.simplified_journal.id,
            }
        )

        # create room type
        cls.room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
                "list_price": 25,
            }
        )

        # create rooms
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.property.id,
                "name": "Double 101",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
            }
        )

        cls.room2 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.property.id,
                "name": "Double 102",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
            }
        )

        cls.room3 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.property.id,
                "name": "Double 103",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
            }
        )

        # res.partner
        cls.partner_id = cls.env["res.partner"].create(
            {
                "name": "Miguel",
                "vat": "45224522J",
                "country_id": cls.env.ref("base.es").id,
                "city": "Madrid",
                "zip": "28013",
                "street": "Calle de la calle",
            }
        )

        # create a sale channel
        cls.sale_channel_direct1 = cls.env["pms.sale.channel"].create(
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
                "list_price": 25,
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
        journals.inbound_payment_method_line_ids.allowed_on_pms = True

    def _test_invoice_full_folio(self):
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
        r1.flush_recordset()
        # ASSERT
        self.assertEqual(
            state_expected,
            r1.folio_id.invoice_status,
            "The status after a full invoice folio isn't correct",
        )

    def _test_invoice_partial_folio_by_steps(self):
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
            r1.folio_id.sale_line_ids.filtered(lambda r: not r.display_type)[0].id
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
            r1.folio_id.sale_line_ids.filtered(lambda r: not r.display_type)[0].id
        ] = 1
        r1.folio_id._create_invoices(
            lines_to_invoice=dict_lines,
            partner_invoice_id=self.env.ref("base.res_partner_1").id,
        )

        # test does not work without invalidating cache
        self.env["account.move"].invalidate_recordset()

        self.assertNotEqual(
            "invoiced",
            r1.folio_id.invoice_status,
            "The status after a partial invoicing is not correct",
        )
        # qty to 2 to 1st folio sale line
        dict_lines[
            r1.folio_id.sale_line_ids.filtered(lambda r: not r.display_type)[0].id
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
                "adults": True,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
                "pms_property_id": self.property.id,
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
                "adults": True,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
                "pms_property_id": self.property.id,
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
            "The quantity of invoiced board services "
            "don't match between folio and invoice",
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
                "adults": True,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
                "pms_property_id": self.property.id,
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

    def _create_invoiced_reservation(self, nights=3):
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=nights),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner_id.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        reservation.folio_id._create_invoices().action_post()
        return reservation

    def _room_sale_lines(self, reservation):
        return reservation.folio_id.sale_line_ids.filtered(
            lambda line: line.reservation_id == reservation
            and not line.display_type
            and not line.service_id
        )

    def test_extend_invoiced_stay_with_cheaper_nights(self):
        """
        Check that an invoiced stay can be extended with cheaper nights.
        ------------
        read_group sorts the nights of a reservation by price and they were
        paired with the existing sale lines by position, so a new night
        cheaper than the invoiced ones handed its price to the invoiced sale
        line and the locked folio check refused the whole change.
        """
        # ARRANGE
        reservation = self._create_invoiced_reservation()
        invoiced_line = self._room_sale_lines(reservation)
        invoiced_price = invoiced_line.price_unit
        invoiced_nights = invoiced_line.reservation_line_ids

        # ACT
        reservation.write(
            {
                "reservation_line_ids": [
                    (
                        0,
                        0,
                        {
                            "date": reservation.checkout + datetime.timedelta(days=i),
                            "price": invoiced_price - 5,
                            "room_id": reservation.preferred_room_id.id,
                        },
                    )
                    for i in range(2)
                ]
            }
        )

        # ASSERT
        self.assertEqual(
            (invoiced_line.price_unit, invoiced_line.reservation_line_ids),
            (invoiced_price, invoiced_nights),
            "The invoiced sale line should keep its price and nights",
        )
        new_line = self._room_sale_lines(reservation) - invoiced_line
        self.assertEqual(
            (new_line.price_unit, new_line.product_uom_qty),
            (invoiced_price - 5, 2),
            "The new nights should go to a new sale line with their price",
        )

    def test_advance_checkin_of_invoiced_stay_with_cheaper_night(self):
        """
        Check that an invoiced stay can start earlier with a cheaper night.
        ------------
        The new night sorts first by date and by price, and no sale line
        holds it yet. It must not take the invoiced sale line, which still
        belongs to the invoiced nights.
        """
        # ARRANGE
        reservation = self._create_invoiced_reservation()
        invoiced_line = self._room_sale_lines(reservation)
        invoiced_price = invoiced_line.price_unit

        # ACT
        reservation.write(
            {
                "reservation_line_ids": [
                    (
                        0,
                        0,
                        {
                            "date": reservation.checkin - datetime.timedelta(days=1),
                            "price": invoiced_price - 5,
                            "room_id": reservation.preferred_room_id.id,
                        },
                    )
                ]
            }
        )

        # ASSERT
        self.assertEqual(
            (invoiced_line.price_unit, invoiced_line.product_uom_qty),
            (invoiced_price, 3),
            "The invoiced sale line should keep its price and nights",
        )
        room_lines = self._room_sale_lines(reservation).sorted("sequence")
        self.assertEqual(
            room_lines.mapped("price_unit"),
            [invoiced_price - 5, invoiced_price],
            "The earlier night should come first in the folio",
        )

    def test_add_cheaper_service_line_to_invoiced_service(self):
        """
        Check that an invoiced service accepts a new cheaper day.
        ------------
        Service lines were paired with their sale lines by position too, so
        the same locked folio error was raised for services.
        """
        # ARRANGE
        product = self.env["product.product"].create(
            {"name": "Test Product 1", "per_day": True, "list_price": 10}
        )
        reservation = self.env["pms.reservation"].create(
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
        service = self.env["pms.service"].create(
            {
                "is_board_service": False,
                "product_id": product.id,
                "reservation_id": reservation.id,
            }
        )
        reservation.folio_id._create_invoices().action_post()
        invoiced_line = reservation.folio_id.sale_line_ids.filtered(
            lambda line: line.service_id == service
        )
        invoiced_price = invoiced_line.price_unit
        invoiced_qty = invoiced_line.product_uom_qty

        # ACT
        service.write(
            {
                "service_line_ids": [
                    (
                        0,
                        0,
                        {
                            "date": max(service.service_line_ids.mapped("date"))
                            + datetime.timedelta(days=1),
                            "price_unit": invoiced_price - 2,
                            "day_qty": 1,
                        },
                    )
                ]
            }
        )

        # ASSERT
        self.assertEqual(
            (invoiced_line.price_unit, invoiced_line.product_uom_qty),
            (invoiced_price, invoiced_qty),
            "The invoiced service sale line should keep its price and quantity",
        )
        new_line = (
            reservation.folio_id.sale_line_ids.filtered(
                lambda line: line.service_id == service
            )
            - invoiced_line
        )
        self.assertEqual(
            new_line.price_unit,
            invoiced_price - 2,
            "The new day should go to a new sale line with its price",
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
