import datetime

from odoo import fields
from odoo.exceptions import UserError

from .common import TestPms


class TestPmsMultiproperty(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pms_property2 = cls.env["pms.property"].create(
            {
                "name": "Pms_property_test2",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )

        cls.pms_property3 = cls.env["pms.property"].create(
            {
                "name": "Pms_property_test3",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )

    def test_availability_closed_no_room_type_check_property(self):
        """
        Check that availability rules are applied to the correct properties.
        ----------
        Check that for that date test_property1 doesnt have rooms available
        (of that type:room_type1),
        instead, property2 has room_type1 available
        """
        # ARRANGE
        self.pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        self.availability_plan1 = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.pricelist2.id])],
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
            }
        )
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
                "name": "Special Room Test",
                "default_code": "SP_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Double 201 test",
                "room_type_id": self.room_type1.id,
                "capacity": 2,
            }
        )
        # pms.room
        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property2.id,
                "name": "Double 202 test",
                "room_type_id": self.room_type1.id,
                "capacity": 2,
            }
        )
        self.room_type_availability_rule1 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.availability_plan1.id,
                "room_type_id": self.room_type1.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
                "pms_property_id": self.pms_property1.id,
            }
        )
        self.room_type_availability_rule2 = self.env[
            "pms.availability.plan.rule"
        ].create(
            {
                "availability_plan_id": self.availability_plan1.id,
                "room_type_id": self.room_type1.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "pms_property_id": self.pms_property2.id,
            }
        )

        properties = [
            {"property": self.pms_property1.id, "value": False},
            {"property": self.pms_property2.id, "value": True},
        ]

        for p in properties:
            with self.subTest(k=p):
                # ACT
                pms_property = self.env["pms.property"].browse(p["property"])
                pms_property = pms_property.with_context(
                    checkin=fields.date.today(),
                    checkout=(
                        fields.datetime.today() + datetime.timedelta(days=2)
                    ).date(),
                    room_type_id=self.room_type1.id,
                    pricelist_id=self.pricelist2.id,
                )
                rooms_avail = pms_property.free_room_ids

                # ASSERT
                self.assertEqual(
                    len(rooms_avail) > 0, p["value"], "Availability is not correct"
                )

    # AMENITY
    def test_amenity_property_not_allowed(self):
        """
        Creation of a Amenity with Properties incompatible with it Amenity Type

        +-----------------------------------+-----------------------------------+
        |  Amenity Type (TestAmenityType1)  |      Amenity (TestAmenity1)       |
        +-----------------------------------+-----------------------------------+
        |      Property1 - Property2        | Property1 - Property2 - Property3 |
        +-----------------------------------+-----------------------------------+
        """
        # ARRANGE
        AmenityType = self.env["pms.amenity.type"]
        Amenity = self.env["pms.amenity"]
        amenity_type1 = AmenityType.create(
            {
                "name": "TestAmenityType1",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(UserError), self.cr.savepoint():
            Amenity.create(
                {
                    "name": "TestAmenity1",
                    "pms_amenity_type_id": amenity_type1.id,
                    "pms_property_ids": [
                        (
                            6,
                            0,
                            [
                                self.pms_property1.id,
                                self.pms_property2.id,
                                self.pms_property3.id,
                            ],
                        )
                    ],
                }
            )

    # AVAILABILITY PLAN RULES
    def test_check_property_availability_room_type(self):
        """
        Check integrity between availability properties and room_type properties.
        Test cases when creating a availability_rule:
        Allowed properties:
        Room Type(room_type1)         --> pms_property1, pms_property_4
        Availability Plan(availability_example)   --> pms_property1, pms_property2

        Both cases throw an exception:
        # 1:Rule for property2,
        #    it is allowed in availability_plan but not in room_type
        # 2:Rule for property4,
        #    it is allowed in room_type, but not in availability_plan
        """
        # ARRANGE
        self.pms_property4 = self.env["pms.property"].create(
            {
                "name": "Property 3",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        # create new room_type
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property4.id),
                ],
                "name": "Special Room Test",
                "default_code": "SP_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        # ACT
        self.availability_plan1 = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.pricelist2.id])],
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
            }
        )
        self.availability_rule1 = self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.availability_plan1.id,
                "room_type_id": self.room_type1.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
                "pms_property_id": self.pms_property1.id,
            }
        )

        test_cases = [
            {
                "pms_property_id": self.pms_property2.id,
            },
            {
                "pms_property_id": self.pms_property4.id,
            },
        ]
        # ASSERT
        for test_case in test_cases:
            with self.subTest(k=test_case):
                with self.assertRaises(UserError):
                    self.availability_rule1.pms_property_id = test_case[
                        "pms_property_id"
                    ]

    # BOARD SERVICE LINE
    def test_pms_bsl_product_property_integrity(self):
        """
        Creation of a board service line without property, of a product
        only available for a specific property.
        """
        # ARRANGE
        product1 = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )
        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.line"].create(
                {
                    "product_id": product1.id,
                    "pms_board_service_id": board_service1.id,
                }
            )

    def test_pms_bsl_board_service_property_integrity(self):
        """
        Creation of a board service line without property, of board service
        only available for a specific property.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        product1 = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )

        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
                "pms_property_ids": [pms_property2.id],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.line"].create(
                {
                    "product_id": product1.id,
                    "pms_board_service_id": board_service1.id,
                }
            )

    def test_pms_bsl_board_service_line_prop_integrity(self):
        """
        Creation of a board service line with a specific property,
        of board service without property.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        product1 = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )
        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.line"].create(
                {
                    "product_id": product1.id,
                    "pms_board_service_id": board_service1.id,
                    "pms_property_ids": [pms_property2.id],
                }
            )

    # BOARD SERVICE ROOM TYPE
    def test_create_rt_props_gt_bs_props(self):
        """
        Create board service for a room type and the room type
        have MORE properties than the board service.
        Record of board_service_room_type should contain the
        board service properties.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )

        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, pms_property2.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service_test = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_test.id,
                "pms_property_id": self.pms_property1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            board_service_test.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " board service properties.",
        )

    def test_create_rt_props_lt_bs_props(self):
        """
        Create board service for a room type and the room type
        have LESS properties than the board service.
        Record of board_service_room_type should contain the
        room types properties.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service1 = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id, pms_property2.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type1.id,
                "pms_board_service_id": board_service1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            room_type1.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " room types properties.",
        )

    def test_create_rt_props_eq_bs_props(self):
        """
        Create board service for a room type and the room type
        have THE SAME properties than the board service.
        Record of board_service_room_type should contain the
        room types properties that matchs with the board
        service properties
        """
        # ARRANGE
        room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service1 = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type1.id,
                "pms_board_service_id": board_service1.id,
            }
        )
        # ASSERT
        self.assertTrue(
            new_bsrt.pms_property_ids.ids == room_type1.pms_property_ids.ids
            and new_bsrt.pms_property_ids.ids == board_service1.pms_property_ids.ids,
            "Record of board_service_room_type should contain the room "
            "types properties and matchs with the board service properties",
        )

    def test_create_rt_no_props_and_bs_props(self):
        """
        Create board service for a room type and the room type
        hasn't properties but the board services.
        Record of board_service_room_type should contain the
        board service properties.
        """
        # ARRANGE
        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service1 = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
                "pms_property_ids": [self.pms_property1.id],
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type1.id,
                "pms_board_service_id": board_service1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            board_service1.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " board service properties.",
        )

    def test_create_rt_props_and_bs_no_props(self):
        """
        Create board service for a room type and the board service
        hasn't properties but the room type.
        Record of board_service_room_type should contain the
        room type properties.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, pms_property2.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service1 = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type1.id,
                "pms_board_service_id": board_service1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            new_bsrt.pms_property_ids.ids,
            room_type1.pms_property_ids.ids,
            "Record of board_service_room_type should contain the"
            " room type properties.",
        )

    def test_create_rt_no_props_and_bs_no_props(self):
        """
        Create board service for a room type and the board service
        has no properties and neither does the room type
        Record of board_service_room_type shouldnt contain properties.
        """
        # ARRANGE

        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
                "price": 25,
            }
        )
        board_service1 = self.board_service = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service",
                "default_code": "TPS",
            }
        )
        # ACT
        new_bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type1.id,
                "pms_board_service_id": board_service1.id,
            }
        )
        # ASSERT
        self.assertFalse(
            new_bsrt.pms_property_ids.ids,
            "Record of board_service_room_type shouldnt contain properties.",
        )

    def test_pms_bsrtl_product_property_integrity(self):
        """
        Creation of a board service room type line without property, of a product
        only available for a specific property.
        """
        # ARRANGE

        product1 = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": self.pms_property1}
        )
        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )
        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "Type1",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": board_service1.id,
                "pms_room_type_id": room_type1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service room type line shouldnt be created."
        ):
            self.env["pms.board.service.room.type.line"].create(
                {
                    "pms_board_service_room_type_id": board_service_room_type1.id,
                    "product_id": product1.id,
                }
            )

    def test_pms_bsrtl_board_service_line_prop_integrity(self):
        """
        Creation of a board service room type line with a specific property,
        of board service without property.
        """
        # ARRANGE
        product1 = self.env["product.product"].create(
            {"name": "Product", "pms_property_ids": [self.pms_property1.id]}
        )
        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board Service",
                "default_code": "CB",
            }
        )

        room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Room Type",
                "default_code": "Type1",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": board_service1.id,
                "pms_room_type_id": room_type1.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            UserError, msg="Board service line shouldnt be created."
        ):
            self.env["pms.board.service.room.type.line"].create(
                {
                    "product_id": product1.id,
                    "pms_property_ids": [self.pms_property2.id],
                    "pms_board_service_room_type_id": board_service_room_type1.id,
                }
            )

    # PMS.FOLIO
    def test_folio_closure_reason_consistency_properties(self):
        """
        Check the multiproperty consistency between
        clousure reasons and folios
        -------
        create multiproperty scenario (3 properties in total) and
        a new clousure reason in pms_property1 and pms_property2, then, create
        a new folio in property3 and try to set the clousure_reason
        waiting a error property consistency.
        """
        # ARRANGE
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

    # PRICELIST
    def test_inconsistency_property_pricelist_item(self):
        """
        Check a pricelist item and its pricelist are inconsistent with the property.
        Create a pricelist item that belongs to a property and check if
        a pricelist that belongs to a diferent one, cannot be created.
        """
        # ARRANGE
        # ACT & ASSERT
        self.pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                    (4, self.pms_property2.id),
                ],
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "SIN",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )
        with self.assertRaises(UserError):
            self.item1 = self.env["product.pricelist.item"].create(
                {
                    "name": "item_1",
                    "applied_on": "0_product_variant",
                    "product_id": self.room_type1.product_id.id,
                    "date_start": datetime.datetime.today(),
                    "date_end": datetime.datetime.today() + datetime.timedelta(days=1),
                    "fixed_price": 40.0,
                    "pricelist_id": self.pricelist2.id,
                    "pms_property_ids": [self.pms_property3.id],
                }
            )

    def test_inconsistency_cancelation_rule_property(self):
        """
        Check a cancelation rule and its pricelist are inconsistent with the property.
        Create a cancelation rule that belongs to a two properties and check if
        a pricelist that belongs to a diferent properties, cannot be created.
        """
        # ARRANGE

        Pricelist = self.env["product.pricelist"]
        # ACT
        self.cancelation_rule1 = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.pms_property1.id, self.pms_property3.id],
            }
        )
        # ASSERT
        with self.assertRaises(UserError):
            Pricelist.create(
                {
                    "name": "Pricelist Test",
                    "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                    "cancelation_rule_id": self.cancelation_rule1.id,
                    "is_pms_available": True,
                }
            )

    def test_inconsistency_availability_plan_property(self):
        """
        Check a availability plan and its pricelist are inconsistent with the property.
        Create a availability plan that belongs to a two properties and check if
        a pricelist that belongs to a diferent properties, cannot be created.
        """
        self.availability_plan1 = self.env["pms.availability.plan"].create(
            {"name": "Availability Plan", "pms_property_ids": [self.pms_property1.id]}
        )
        with self.assertRaises(UserError):
            self.env["product.pricelist"].create(
                {
                    "name": "Pricelist",
                    "pms_property_ids": [self.pms_property2.id],
                    "availability_plan_id": self.availability_plan1.id,
                    "is_pms_available": True,
                }
            )

    def test_multiproperty_checks(self):
        """
        # TEST CASE
        Multiproperty checks in reservation
        +---------------+------+------+------+----+----+
        |  reservation  |           property1          |
        +---------------+------+------+------+----+----+
        |      room     |           property2          |
        |   room_type   |      property2, property3    |
        | board_service |      property2, property3    |
        |   pricelist   |      property2, property3    |
        +---------------+------+------+------+----+----+
        """
        # ARRANGE
        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board Service Test",
                "default_code": "CB",
            }
        )
        host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "mobile": "654667733",
                "email": "miguel@example.com",
            }
        )
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
        self.reservation1 = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=1),
                "pms_property_id": self.pms_property1.id,
                "partner_id": host1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        room_type_test = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, self.pms_property3.id),
                    (4, self.pms_property2.id),
                ],
                "name": "Single",
                "default_code": "SIN",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )

        room = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property2.id,
                "room_type_id": room_type_test.id,
            }
        )

        pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "pricelist_test",
                "pms_property_ids": [
                    (4, self.pms_property2.id),
                    (4, self.pms_property3.id),
                ],
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )

        board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": self.board_service1.id,
                "pms_room_type_id": room_type_test.id,
                "pms_property_ids": [self.pms_property2.id, self.pms_property3.id],
            }
        )
        test_cases = [
            {"preferred_room_id": room.id},
            {"room_type_id": room_type_test.id},
            {"pricelist_id": pricelist2.id},
            {"board_service_room_id": board_service_room_type1.id},
        ]

        for test_case in test_cases:
            with self.subTest(k=test_case):
                with self.assertRaises(UserError):
                    self.reservation1.write(test_case)

    # ROOM
    def test_inconsistency_room_ubication_property(self):
        """
        Room property and its ubication properties are inconsistent.
        A Room with property that is not included in available properties
        for its ubication cannot be created.
        """
        # ARRANGE
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "SI",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )
        ubication1 = self.env["pms.ubication"].create(
            {
                "name": "UbicationTest",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                ],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            UserError,
            msg="The room should not be created if its property is not included "
            "in the available properties for its ubication.",
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property2.id,
                    "room_type_id": self.room_type1.id,
                    "ubication_id": ubication1.id,
                }
            )

    def test_consistency_room_ubication_property(self):
        """
        Room property and its ubication properties are consistent.
        A Room with property included in available properties
        for its ubication can be created.
        """
        # ARRANGE
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "SI",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )
        ubication1 = self.env["pms.ubication"].create(
            {
                "name": "UbicationTest",
                "pms_property_ids": [
                    (4, self.pms_property1.id),
                ],
            }
        )
        # ACT
        new_room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
                "ubication_id": ubication1.id,
            }
        )
        # ASSERT
        self.assertIn(
            new_room1.pms_property_id,
            ubication1.pms_property_ids,
            "The room should be created if its property belongs to the availabe"
            "properties for its ubication.",
        )

    def test_inconsistency_room_type_property(self):
        """
        Room property and its room type properties are inconsistent.
        A Room with property that is not included in available properties
        for its room type cannot be created.
        """
        # ARRANGE
        self.pms_property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "SI",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )
        # ACT & ARRANGE
        with self.assertRaises(
            UserError,
            msg="The room should not be created if its property is not included "
            "in the available properties for its room type.",
        ):
            self.env["pms.room"].create(
                {
                    "name": "Room 101",
                    "pms_property_id": self.pms_property3.id,
                    "room_type_id": self.room_type1.id,
                }
            )

    def test_consistency_room_type_property(self):
        """
        Room property and its room type properties are inconsistent.
        A Room with property included in available properties
        for its room type can be created.
        """
        # ARRANGE
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "SI",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )
        # ACT
        room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )
        # ASSERT
        self.assertIn(
            room1.pms_property_id,
            self.room_type1.pms_property_ids,
            "The room should be created if its property is included "
            "in the available properties for its room type.",
        )
