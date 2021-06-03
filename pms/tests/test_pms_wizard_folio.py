import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.tests import common


@freeze_time("1980-12-01")
class TestPmsWizardMassiveChanges(common.SavepointCase):
    def create_common_scenario(self):
        # PRICELIST CREATION
        self.test_pricelist = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
            }
        )
        self.test_pricelist.flush()

        # AVAILABILITY PLAN CREATION
        self.test_availability_plan = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist.id])],
            }
        )
        self.test_availability_plan.flush()

        # SEQUENCES
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
        # PROPERTY CREATION (WITH DEFAULT PRICELIST AND AVAILABILITY PLAN
        self.test_property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist.id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        self.test_property.flush()

        # CREATION OF ROOM TYPE CLASS
        self.test_room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "default_code": "ROOM"}
        )
        self.test_room_type_class.flush()

        # CREATION OF ROOM TYPE (WITH ROOM TYPE CLASS)
        self.test_room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Single Test",
                "default_code": "SNG_Test",
                "class_id": self.test_room_type_class.id,
                "list_price": 25.0,
            }
        )
        self.test_room_type_single.flush()

        # CREATION OF ROOM TYPE (WITH ROOM TYPE CLASS)
        self.test_room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.test_room_type_class.id,
                "list_price": 40.0,
            }
        )
        self.test_room_type_double.flush()

        # pms.room
        self.test_room1_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 201 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        self.test_room1_double.flush()

        # pms.room
        self.test_room2_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 202 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        self.test_room2_double.flush()

        # pms.room
        self.test_room3_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 203 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        self.test_room3_double.flush()

        # pms.room
        self.test_room4_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 204 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        self.test_room4_double.flush()

        # pms.room
        self.test_room1_single = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Single 101 test",
                "room_type_id": self.test_room_type_single.id,
                "capacity": 1,
            }
        )
        self.test_room1_single.flush()

        # pms.room
        self.test_room2_single = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Single 102 test",
                "room_type_id": self.test_room_type_single.id,
                "capacity": 1,
            }
        )
        self.test_room2_single.flush()

        # res.partner
        self.partner_id = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "phone": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.partner_id.flush()

    def test_price_wizard_correct(self):
        # TEST CASE
        # Set values for the wizard and the total price is correct
        # Also check the discount is correctly applied to get
        #                               the total folio price

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        days = (checkout - checkin).days
        num_double_rooms = 4
        discounts = [
            {
                "discount": 0,
                "expected_price": days
                * self.test_room_type_double.list_price
                * num_double_rooms,
            },
            {
                "discount": 0.5,
                "expected_price": (
                    days * self.test_room_type_double.list_price * num_double_rooms
                )
                * 0.5,
            },
        ]

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pms_property_id": self.test_property.id,
                "pricelist_id": self.test_pricelist.id,
            }
        )

        # force pricelist load
        wizard_folio.flush()

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.test_property.id),
            ]
        )

        # set value for room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", str(self.test_room_type_double.id)),
                ("value", "=", num_double_rooms),
            ]
        )

        lines_availability_test[0].num_rooms_selected = value
        for discount in discounts:
            with self.subTest(k=discount):
                # ACT
                wizard_folio.discount = discount["discount"]

                # ASSERT
                self.assertEqual(
                    wizard_folio.total_price_folio,
                    discount["expected_price"],
                    "The total price calculation is wrong",
                )

    def test_price_wizard_correct_pricelist_applied(self):
        # TEST CASE
        # Set values for the wizard and the total price is correct
        # (pricelist applied)

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        days = (checkout - checkin).days

        # num. rooms of type double to book
        num_double_rooms = 4

        # price for today
        price_today = 38.0

        # expected price
        expected_price_total = days * price_today * num_double_rooms

        # set pricelist item for current day
        product_tmpl = self.test_room_type_double.product_id.product_tmpl_id
        pricelist_item = self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.test_pricelist.id,
                "date_start_consumption": checkin,
                "date_end_consumption": checkin,
                "compute_price": "fixed",
                "applied_on": "1_product",
                "product_tmpl_id": product_tmpl.id,
                "fixed_price": price_today,
                "min_quantity": 0,
                "pms_property_ids": product_tmpl.pms_property_ids.ids,
            }
        )
        pricelist_item.flush()

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.test_property.id),
            ]
        )

        # set value for room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", str(self.test_room_type_double.id)),
                ("value", "=", num_double_rooms),
            ]
        )

        # ACT
        lines_availability_test[0].num_rooms_selected = value

        # ASSERT
        self.assertEqual(
            wizard_folio.total_price_folio,
            expected_price_total,
            "The total price calculation is wrong",
        )

    # REVIEW: This test is set to check min qty, but the workflow price, actually,
    # always is set to 1 qty and the min_qty cant be applied.
    # We could set qty to number of rooms??

    # def test_price_wizard_correct_pricelist_applied_min_qty_applied(self):
    #     # TEST CASE
    #     # Set values for the wizard and the total price is correct
    #     # (pricelist applied)

    #     # ARRANGE
    #     # common scenario
    #     self.create_common_scenario()

    #     # checkin & checkout
    #     checkin = fields.date.today()
    #     checkout = fields.date.today() + datetime.timedelta(days=1)
    #     days = (checkout - checkin).days

    #     # set pricelist item for current day
    #     product_tmpl_id = self.test_room_type_double.product_id.product_tmpl_id.id
    #     pricelist_item = self.env["product.pricelist.item"].create(
    #         {
    #             "pricelist_id": self.test_pricelist.id,
    #             "date_start_consumption": checkin,
    #             "date_end_consumption": checkin,
    #             "compute_price": "fixed",
    #             "applied_on": "1_product",
    #             "product_tmpl_id": product_tmpl_id,
    #             "fixed_price": 38.0,
    #             "min_quantity": 4,
    #         }
    #     )
    #     pricelist_item.flush()

    #     # create folio wizard with partner id => pricelist & start-end dates
    #     wizard_folio = self.env["pms.folio.wizard"].create(
    #         {
    #             "start_date": checkin,
    #             "end_date": checkout,
    #             "partner_id": self.partner_id.id,
    #             "pricelist_id": self.test_pricelist.id,
    #         }
    #     )
    #     wizard_folio.flush()

    #     # availability items belonging to test property
    #     lines_availability_test = self.env["pms.folio.availability.wizard"].search(
    #         [
    #             ("room_type_id.pms_property_ids", "in", self.test_property.id),
    #         ]
    #     )

    #     test_cases = [
    #         {
    #             "num_rooms": 3,
    #             "expected_price": 3 * self.test_room_type_double.list_price * days,
    #         },
    #         {"num_rooms": 4, "expected_price": 4 * pricelist_item.fixed_price * days},
    #     ]
    #     import wdb; wdb.set_trace()
    #     for tc in test_cases:
    #         with self.subTest(k=tc):
    #             # ARRANGE
    #             # set value for room type double
    #             value = self.env["pms.num.rooms.selection"].search(
    #                 [
    #                     ("room_type_id", "=", str(self.test_room_type_double.id)),
    #                     ("value", "=", tc["num_rooms"]),
    #                 ]
    #             )
    #             # ACT
    #             lines_availability_test[0].num_rooms_selected = value

    #             # ASSERT
    #             self.assertEqual(
    #                 wizard_folio.total_price_folio,
    #                 tc["expected_price"],
    #                 "The total price calculation is wrong",
    #             )

    def test_check_create_folio(self):
        # TEST CASE
        # Set values for the wizard check that folio is created

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.test_property.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", str(self.test_room_type_double.id)),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value

        # ACT
        wizard_folio.create_folio()

        # ASSERT
        folio = self.env["pms.folio"].search_count(
            [("partner_id", "=", self.partner_id.id)]
        )

        self.assertTrue(folio, "Folio not created.")

    def test_check_create_reservations(self):
        # TEST CASE
        # Set values for the wizard check that reservations are created

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.test_property.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", str(self.test_room_type_double.id)),
                ("value", "=", 2),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 2
        lines_availability_test.flush()
        wizard_folio.flush()

        # ACT
        wizard_folio.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])
        folio.flush()

        # ASSERT
        self.assertEqual(len(folio.reservation_ids), 2, "Reservations  not created.")

    def test_values_folio_created(self):
        # TEST CASE
        # Set values for the wizard and values of folio are correct

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.test_property.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", str(self.test_room_type_double.id)),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1

        # ACT
        wizard_folio.create_folio()
        vals = {
            "partner_id": self.partner_id.id,
            "pricelist_id": self.test_pricelist.id,
        }
        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        # ASSERT
        for key in vals:
            with self.subTest(k=key):
                self.assertEqual(
                    folio[key].id,
                    vals[key],
                    "The value of " + key + " is not correctly established",
                )

    def test_values_reservation_created(self):
        # TEST CASE
        # Set values for the wizard and values of reservations are correct

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.test_property.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", str(self.test_room_type_double.id)),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1

        # ACT
        wizard_folio.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        vals = {
            "folio_id": folio.id,
            "checkin": checkin,
            "checkout": checkout,
            "room_type_id": self.test_room_type_double,
            "partner_id": self.partner_id.id,
            "pricelist_id": folio.pricelist_id.id,
            "pms_property_id": self.test_property.id,
        }

        # ASSERT
        for reservation in folio.reservation_ids:
            for key in vals:
                with self.subTest(k=key):
                    self.assertEqual(
                        reservation[key].id
                        if key
                        in ["folio_id", "partner_id", "pricelist_id", "pms_property_id"]
                        else reservation[key],
                        vals[key],
                        "The value of " + key + " is not correctly established",
                    )

    def test_reservation_line_discounts(self):
        # TEST CASE
        # set a discount and its applied to the reservation line

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)
        discount = 0.5

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "discount": discount,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        # availability items belonging to test property
        lines_availability_test = self.env["pms.folio.availability.wizard"].search(
            [
                ("room_type_id.pms_property_ids", "in", self.test_property.id),
            ]
        )
        # set one room type double
        value = self.env["pms.num.rooms.selection"].search(
            [
                ("room_type_id", "=", str(self.test_room_type_double.id)),
                ("value", "=", 1),
            ]
        )
        lines_availability_test[0].num_rooms_selected = value
        lines_availability_test[0].value_num_rooms_selected = 1

        # ACT
        wizard_folio.create_folio()

        folio = self.env["pms.folio"].search([("partner_id", "=", self.partner_id.id)])

        # ASSERT
        for reservation in folio.reservation_ids:
            for line in reservation.reservation_line_ids:
                with self.subTest(k=line):
                    self.assertEqual(
                        line.discount,
                        discount * 100,
                        "The discount is not correctly established",
                    )

    def test_check_quota_avail(self):
        # TEST CASE
        # Check avail on room type with quota

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        self.env["pms.availability.plan.rule"].create(
            {
                "quota": 1,
                "room_type_id": self.test_room_type_double.id,
                "availability_plan_id": self.test_availability_plan.id,
                "date": fields.date.today(),
                "pms_property_id": self.test_property.id,
            }
        )

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        room_type_plan_avail = wizard_folio.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        ).num_rooms_available

        # ASSERT

        self.assertEqual(room_type_plan_avail, 1, "Quota not applied in Wizard Folio")

    def test_check_min_stay_avail(self):
        # TEST CASE
        # Check avail on room type with quota

        # ARRANGE
        # common scenario
        self.create_common_scenario()

        # checkin & checkout
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=1)

        self.env["pms.availability.plan.rule"].create(
            {
                "min_stay": 3,
                "room_type_id": self.test_room_type_double.id,
                "availability_plan_id": self.test_availability_plan.id,
                "date": fields.date.today(),
                "pms_property_id": self.test_property.id,
            }
        )

        # create folio wizard with partner id => pricelist & start-end dates
        wizard_folio = self.env["pms.folio.wizard"].create(
            {
                "start_date": checkin,
                "end_date": checkout,
                "partner_id": self.partner_id.id,
                "pricelist_id": self.test_pricelist.id,
                "pms_property_id": self.test_property.id,
            }
        )
        wizard_folio.flush()

        room_type_plan_avail = wizard_folio.availability_results.filtered(
            lambda r: r.room_type_id.id == self.test_room_type_double.id
        ).num_rooms_available

        # ASSERT

        self.assertEqual(room_type_plan_avail, 0, "Quota not applied in Wizard Folio")
