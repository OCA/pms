import datetime

from odoo.tests import common


class TestPmsFolioInvoice(common.SavepointCase):
    def setUp(self):
        super(TestPmsFolioInvoice, self).setUp()

    def create_common_scenario(self):
        # create a room type availability
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
        self.room_type_availability = self.env["pms.availability.plan"].create(
            {"name": "Availability plan for TEST"}
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
        self.demo_user = self.env.ref("base.user_admin")

    def test_invoice_full_folio(self):
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        r1.flush()
        r1.folio_id.flush()
        r1.folio_id.sale_line_ids.flush()
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
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        dict_lines = dict()
        # qty to 1 to 1st folio sale line
        dict_lines[
            r1.folio_id.sale_line_ids.filtered(lambda l: not l.display_type)[0].id
        ] = 1
        r1.folio_id._create_invoices(lines_to_invoice=dict_lines)

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
        r1.folio_id._create_invoices(lines_to_invoice=dict_lines)

        self.assertEqual(
            "invoiced",
            r1.folio_id.invoice_status,
            "The status after an invoicing is not correct",
        )

    def test_invoice_partial_folio_diferent_partners(self):
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=3),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        dict_lines = dict()
        # qty to 1 to 1st folio sale line
        dict_lines[
            r1.folio_id.sale_line_ids.filtered(lambda l: not l.display_type)[0].id
        ] = 1
        r1.folio_id._create_invoices(
            lines_to_invoice=dict_lines,
            partner_invoice_id=self.env.ref("base.res_partner_1"),
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
            partner_invoice_id=self.env.ref("base.res_partner_12"),
        )
        self.assertNotEqual(
            r1.folio_id.move_ids.mapped("partner_id")[0],
            r1.folio_id.move_ids.mapped("partner_id")[1],
            "The status after an invoicing is not correct",
        )

    def test_invoice_partial_folio_wrong_qtys(self):
        # ARRANGE
        self.create_common_scenario()
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.room_type_double.id,
                "partner_id": self.env.ref("base.res_partner_12").id,
            }
        )
        tcs = [-1, 0, 3]

        for tc in tcs:
            with self.subTest(k=tc):
                with self.assertRaises(ValueError):
                    # ARRANGE
                    dict_lines = dict()
                    dict_lines[
                        r1.folio_id.sale_line_ids.filtered(
                            lambda l: not l.display_type
                        )[0].id
                    ] = tc
                    r1.folio_id._create_invoices(lines_to_invoice=dict_lines)
                    # test does not work without invalidating cache
                    self.env["account.move"].invalidate_cache()

    # TODO: complete tests
    def _test_invoice_folio(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts"""

    def _test_invoice_by_days_folio(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts in a specific segment of days (reservation lines)"""

    def _test_invoice_by_services_folio(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts in a specific segment of services (qtys)"""

    def _test_invoice_board_service(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the related amounts with board service linked"""

    def _test_invoice_line_group_by_room_type_sections(self):
        """Test create and invoice from the Folio, and check qty invoice/to invoice,
        and the grouped invoice lines by room type, by one
        line by unit prices/qty with nights"""

    def _test_autoinvoice_folio(self):
        """ Test create and invoice the cron by partner preconfig automation """

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
