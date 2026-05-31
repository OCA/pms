# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from .common import TestPms


class TestBoardService(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company2 = cls.env["res.company"].create(
            {
                "name": "Company 2",
            }
        )
        cls.pms_property3 = cls.env["pms.property"].create(
            {
                "name": "Property 3",
                "company_id": cls.company2.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )

    def test_create_bs_one_company_inconsistent_code(self):
        """
        Creation of board service with the same code as an existing one
        belonging to the same property should fail.

        PRE:    - board service bs1 exists
                - board_service1 has code c1
                - board_service1 has pms_property1
                - pms_property1 has company company1
        ACT:    - create a new board_service2
                - board_service2 has code c1
                - board_service2 has pms_property1
                - pms_property1 has company company1
        POST:   - Integrity error: the room type already exists
                - board_service2 not created
        """
        # ARRANGE
        # board_service1
        self.env["pms.board.service"].create(
            {
                "name": "Board service bs1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The board service has been created and it shouldn't"
        ):
            # board_service2
            self.env["pms.board.service"].create(
                {
                    "name": "Board service bs2",
                    "default_code": "c1",
                    "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                }
            )

    def test_create_bs_several_companies_inconsistent_code(self):
        """
        Creation of board service with properties and one of its
        properties has the same code on its board services should fail.

        PRE:    - board service bs1 exists
                - board_service1 has code c1
                - board_service1 has property pms_property1
                - pms_property1 has company company1
        ACT:    - create a new board_service2
                - board_service2 has code c1
                - board_service2 has property pms_property1, pms_property2,
                    pms_property3
                - pms_property1, pms_property2 has company company1
                - pms_property3 has company company2
        POST:   - Integrity error: the board service already exists
                - board_service2 not created
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        # board_service1
        self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="The board service has been created and it shouldn't"
        ):
            # board_service2
            self.env["pms.board.service"].create(
                {
                    "name": "Board service bs2",
                    "default_code": "c1",
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

    def test_search_bs_code_same_company_several_properties(self):
        """
        Checks the search for a board service by code when the board service
        belongs to properties of the same company

        PRE:    - board service bs1 exists
                - board_service1 has code c1
                - board_service1 has 2 properties pms_property1 and pms_property2
                - pms_property_1 and pms_property2 have the same company company1
        ACT:    - search board service with code c1 and pms_property1
                - pms_property1 has company company1
        POST:   - only board_service1 board service found
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property2.id])
                ],
            }
        )
        # ACT
        board_services = self.env["pms.board.service"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )
        # ASSERT
        self.assertEqual(
            board_services.id,
            board_service1.id,
            "Expected board service not found",
        )

    def test_search_bs_code_several_companies_several_properties_not_found(self):
        """
        Checks the search for a board service by code when the board service
        belongs to properties with different companies

        PRE:    - board service bs1 exists
                - board_service1 has code c1
                - board_service1 has 2 properties pms_property1 and pms_property3
                - pms_property1 and pms_property3 have different companies
                - pms_property1 have company company1 and pms_property3 have company2
        ACT:    - search board service with code c1 and property pms_property1
                - pms_property1 has company company1
        POST:   - only board_service1 room type found
        """
        # ARRANGE
        bs1 = self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
            }
        )
        # ACT
        board_services = self.env["pms.board.service"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )
        # ASSERT
        self.assertEqual(board_services.id, bs1.id, "Expected board service not found")

    def test_search_bs_code_no_result(self):
        """
        Search for a specific board service code and its property.
        The board service exists but not in the property given.

        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 with 2 properties pms_property1 and pms_property2
                - pms_property1 and pms_property2 have same company company1
        ACT:    - search board service with code c1 and property pms_property3
                - pms_property3 have company company2
        POST:   - no room type found
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        # board_service1
        self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property2.id])
                ],
            }
        )
        # ACT
        board_services = self.env["pms.board.service"].get_unique_by_property_code(
            self.pms_property3.id, "c1"
        )
        # ASSERT
        self.assertFalse(
            board_services, "Board service found but it should not have found any"
        )

    def test_search_bs_code_present_all_companies_and_properties(self):
        """
        Search for a specific board service and its property.
        The board service exists without property, then
        the search foundS the result.

        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 properties are null
        ACT:    - search board service with code c1 and property pms_property1
                - pms_property1 have company company1
        POST:   - only board_service1 board service found
        """
        # ARRANGE
        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )
        # ACT
        board_services = self.env["pms.board.service"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )
        # ASSERT
        self.assertEqual(
            board_services.id,
            board_service1.id,
            "Expected board service not found",
        )

    def test_search_bs_code_several_companies_several_properties(self):
        """
        Search for a specific board service and its property.
        There is one board service without properties and
        another one with the same code that belongs to 2 properties
        (from different companies)
        The search founds only the board service that match the
        property given.

        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 has 2 properties pms_property1 and pms_property3
                - pms_property1 and pms_property2 have the same company company1
                - board service board_service2 exists
                - board_service2 has code c1
                - board_service2 has no properties
        ACT:    - search board service with code c1 and property pms_property1
                - pms_property1 have company company1
        POST:   - only board_service1 board service found
        """
        # ARRANGE
        board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": [
                    (6, 0, [self.pms_property1.id, self.pms_property3.id])
                ],
            }
        )
        # board_service2
        self.env["pms.board.service"].create(
            {
                "name": "Board service bs2",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )
        # ACT
        board_services = self.env["pms.board.service"].get_unique_by_property_code(
            self.pms_property1.id, "c1"
        )
        # ASSERT
        self.assertEqual(
            board_services.id,
            board_service1.id,
            "Expected board service not found",
        )

    def test_search_bs_code_same_companies_several_properties(self):
        """
        Search for a specific board service and its property.
        There is one board service without properties and
        another one with the same code that belongs to 2 properties
        (same company).
        The search founds only the board service that match the
        property given.

        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 has property pms_property1
                - pms_property1 have the company company1
                - board service board_service2 exists
                - board_service2 has code c1
                - board_service2 has no properties
        ACT:    - search board service with code c1 and pms_property2
                - pms_property2 have company company1
        POST:   - only board_service2 board service found
        """
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.env["pms.board.service"].create(
            {
                "name": "Board service 1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        board_service2 = self.env["pms.board.service"].create(
            {
                "name": "Board service bs2",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )
        # ACT
        board_services = self.env["pms.board.service"].get_unique_by_property_code(
            self.pms_property2.id, "c1"
        )
        # ASSERT
        self.assertEqual(
            board_services.id,
            board_service2.id,
            "Expected board service not found",
        )

    def test_search_bs_code_no_properties(self):
        """
        Search for a specific board service and its property.
        There is one board service without properties and
        another one with the same code that belongs to one property.
        The search founds only the board service that match the
        property given that it's not the same as the 2nd one.

        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 has property pms_property1
                - pms_property1 have the company company1
                - board service board_service2 exists
                - board_service2 has code c1
                - board_service2 has no properties
        ACT:    - search board service with code c1 and property pms_property3
                - pms_property3 have company company2
        POST:   - only board_service2 board service found
        """
        # ARRANGE
        # board_service1
        self.env["pms.board.service"].create(
            {
                "name": "Board service bs1",
                "default_code": "c1",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        board_service2 = self.env["pms.board.service"].create(
            {
                "name": "Board service bs2",
                "default_code": "c1",
                "pms_property_ids": False,
            }
        )
        # ACT
        board_services = self.env["pms.board.service"].get_unique_by_property_code(
            self.pms_property3.id, "c1"
        )
        # ASSERT
        self.assertEqual(
            board_services.id,
            board_service2.id,
            "Expected board service not found",
        )

    def test_archive_board_service_propagates_to_children(self):
        """
        Archiving a board service must cascade ``active=False`` to its
        lines and to its room-type assignments (and their lines), so that
        the archived regime fully disappears from operative selections
        while historical references remain in place.

        PRE:    - board_service bs1 is active
                - bs1 has one line (bsl)
                - bs1 has one room-type assignment (bsrt) with one line (bsrtl)
        ACT:    - bs1.active = False
        POST:   - bsl.active == False
                - bsrt.active == False
                - bsrtl.active == False
                - reactivating bs1 propagates back to all descendants
        """
        # ARRANGE
        product = self.env["product.product"].create(
            {"name": "Bs Product", "is_pms_available": True}
        )
        room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "name": "Room Type Archive Test",
                "default_code": "RTAT",
                "class_id": self.room_type_class1.id,
                "list_price": 30.0,
            }
        )
        board_service = self.env["pms.board.service"].create(
            {
                "name": "Bs Archive Test",
                "default_code": "BSAT",
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
                "board_service_line_ids": [
                    (0, 0, {"product_id": product.id, "adults": True}),
                ],
            }
        )
        bsrt = self.env["pms.board.service.room.type"].create(
            {
                "pms_board_service_id": board_service.id,
                "pms_room_type_id": room_type.id,
                "pms_property_id": self.pms_property1.id,
            }
        )

        # ACT — archive
        board_service.active = False

        # ASSERT — propagation downwards
        bs_line = board_service.with_context(active_test=False).board_service_line_ids
        bsrt_line = bsrt.with_context(active_test=False).board_service_line_ids
        self.assertFalse(bs_line.active, "Board service line was not archived")
        self.assertFalse(
            bsrt.with_context(active_test=False).active,
            "Board service room type was not archived",
        )
        self.assertFalse(
            bsrt_line.active,
            "Board service room type line was not archived",
        )

        # ACT — reactivate
        board_service.with_context(active_test=False).active = True

        # ASSERT — propagation back
        self.assertTrue(bs_line.active, "Board service line was not reactivated")
        self.assertTrue(bsrt.active, "Board service room type was not reactivated")
        self.assertTrue(
            bsrt_line.active,
            "Board service room type line was not reactivated",
        )
