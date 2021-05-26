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

    # external integrity
    def test_external_case_01(self):
        """
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

    def test_external_case_02(self):
        """
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

    def test_single_case_01(self):
        """
        PRE:    - board service bs1 exists
                - board_service1 has code c1
                - board_service1 has 2 properties pms_property1 and pms_property2
                - pms_property_1 and pms_property2 have the same company company1
        ACT:    - search board service with code c1 and pms_property1
                - pms_property1 has company company1
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

    def test_single_case_02(self):
        """
        PRE:    - board service bs1 exists
                - board_service1 has code c1
                - board_service1 has 2 properties pms_property1 and pms_property3
                - pms_property1 and pms_property2 have different companies
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

    def test_single_case_03(self):
        """
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

    def test_single_case_04(self):
        """
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

    # tests with more than one board service
    def test_multiple_case_01(self):
        """
        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 has 2 properties pms_property1 and pms_property2
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

    def test_multiple_case_02(self):
        """
        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 has property pms_property1
                - pms_property1 have the company company1
                - board service board_service2 exists
                - board_service2 has code c1
                - board_service2 has no properties
        ACT:    - search board service with code c1 and pms_property2
                - pms_property2 have company company1
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
        # board_service1
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

    def test_multiple_case_03(self):
        """
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

    def test_multiple_case_04(self):
        """
        PRE:    - board_service1 exists
                - board_service1 has code c1
                - board_service1 has property pms_property1
                - pms_property1 have the company company1
                - room type board_service2 exists
                - board_service2 has code c1
                - board_service2 has no properties
        ACT:    - search board service with code c1 and property pms_property3
                - pms_property3 have company company2
        POST:   - r2 board service found
        """
        # ARRANGE
        # board_service1
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
            self.pms_property3.id, "c1"
        )

        # ASSERT
        self.assertEqual(
            board_services.id, board_service2.id, "Expected room type not found"
        )
