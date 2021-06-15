# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from .common import TestPms


class TestBoardService(TestPms):
    def setUp(self):
        super().setUp()
        self.company2 = self.env["res.company"].create(
            {
                "name": "Company 2",
            }
        )
        self.pms_property3 = self.env["pms.property"].create(
            {
                "name": "Property 3",
                "company_id": self.company2.id,
                "default_pricelist_id": self.pricelist1.id,
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
