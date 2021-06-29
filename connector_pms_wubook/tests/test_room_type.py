# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import xmlrpc.client

import mock

from . import common, server

_logger = logging.getLogger(__name__)


class TestWubookConnectorRoomTypeImport(common.TestWubookConnector):
    # non-existing
    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_non_existing_case01(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type r1 does not exist
        ACT:    - import r1 from property p1
        POST:   - room type r1 imported
                - r1 has the values from the backend
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )

        with backend.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")

        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 2,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter.create(r1w_values)

        # ACT
        backend.import_room_types()

        # ASSERT
        with backend.work_on("channel.wubook.pms.room.type") as work:
            binder = work.component(usage="binder")
        r1 = binder.to_internal(r1w_id, unwrap=True)

        mapped_fields = [
            ("name", "name"),
            ("shortname", "default_code"),
            ("price", "list_price"),
        ]
        odoo_values = (
            [getattr(r1, x) for _, x in mapped_fields]
            + [r1.pms_property_ids]
            + [len(r1.room_ids)]
        )
        wubook_values = (
            [r1w_values.get(x) for x, _ in mapped_fields]
            + [backend.pms_property_id]
            + [r1w_values.get("availability")]
        )

        self.assertListEqual(
            odoo_values,
            wubook_values,
            "The room type data on Odoo does not match the data on Wubook",
        )

    # existing
    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_existing_case01(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type r1 exists
                - r1 has code c1
                - r1 has properties p1, p2
                - p1 and p2 have m1 company both
                - r1 has company null
                - rb1 binding does not exist
                - r1 has class cl1
                - cl1 exists
                - cl1 has property p1, p2
                - cl1r binding does not exist
        ACT:    - import r from property p1
                - p1 has company m1
        POST:   - new binding rb1 is created
                - rb1 contains existing r1 wrapped
                - r1 keeps p1, p2 as a properties
                - r1 company is still null
                - cl1r binding is created
        """
        # mock objects
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        m1 = p1.company_id
        p2 = self.env["pms.property"].create(
            {
                "name": "p2",
                "company_id": m1.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )
        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )
        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "default_code": "RO",
                "pms_property_ids": [(6, 0, [p1.id, p2.id])],
            }
        )

        with backend.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")

        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 1,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter.create(r1w_values)

        r1 = self.env["pms.room.type"].create(
            {
                "name": "Room type r1",
                "list_price": 1.0,
                "default_code": "c1",
                "class_id": cl1.id,
                "pms_property_ids": [(6, 0, [p1.id, p2.id])],
                "company_id": False,
            }
        )

        # ACT
        backend.import_room_types()

        # ASSERT
        with backend.work_on("channel.wubook.pms.room.type") as work:
            binder = work.component(usage="binder")
        r1_obtained = binder.to_internal(r1w_id, unwrap=True)

        with self.subTest():
            self.assertEqual(
                r1.id,
                r1_obtained.id,
                "The room type existing differs from the one imported",
            )
        with self.subTest():
            self.assertCountEqual(
                r1_obtained.pms_property_ids.mapped("id"),
                [p1.id, p2.id],
                "The properties are not the ones existing in the first place",
            )
        with self.subTest():
            self.assertFalse(r1_obtained.company_id, "The company should be null")

    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_existing_case02(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type r1 exists
                - r1 has no properties
                - r1 has no company
                - rb1 binding does not exist
        ACT:    - import r1 from property p1
                - p1 has company m1
        POST:   - new binding rb1 is created
                - rb1 contains existing r1 wrapped
                - r1 keeps without properties
                - r1 company is still null
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )
        with backend.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")

        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 2,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter.create(r1w_values)

        r1 = self.env["pms.room.type"].create(
            {
                "name": "Room type r1",
                "list_price": 1.0,
                "default_code": "c1",
                "class_id": self.ref("pms.pms_room_type_class_0"),
                "pms_property_ids": False,
                "company_id": False,
            }
        )

        # ACT
        backend.import_room_types()

        # ASSERT
        with backend.work_on("channel.wubook.pms.room.type") as work:
            binder = work.component(usage="binder")
        r1_obtained = binder.to_internal(r1w_id, unwrap=True)

        asserts = [
            lambda: self.assertEqual(
                r1.id,
                r1_obtained.id,
                "The room type existing differs from the one imported",
            ),
            lambda: self.assertFalse(
                r1_obtained.pms_property_ids,
                "The properties should be empty as it was on the first place",
            ),
            lambda: self.assertFalse(
                r1_obtained.company_id, "The company should be null"
            ),
        ]
        for assrt in asserts:
            with self.subTest(assrt):
                assrt()

    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_existing_case03(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type r1 exists
                - r1 has property p2
                - p2 have company m1
                - r1 has company null
                - rb1 binding does not exist
        ACT:    - import r1 from property p1
                - p1 has company m1
        POST:   - new binding rb1 is created
                - rb1 contains existing r1 wrapped
                - r1 has properties p1 and p2
                - r1 company is still null
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        m1 = p1.company_id
        p2 = self.env["pms.property"].create(
            {
                "name": "p2",
                "company_id": m1.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )
        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )

        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room type class cl1",
                "default_code": "RO",
                "pms_property_ids": [(6, 0, [p2.id])],
            }
        )

        with backend.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")

        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 1,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter.create(r1w_values)

        r1 = self.env["pms.room.type"].create(
            {
                "name": "Room type r1",
                "list_price": 1.0,
                "default_code": "c1",
                "class_id": cl1.id,
                "pms_property_ids": [(6, 0, [p2.id])],
                "company_id": False,
            }
        )

        # ACT
        backend.import_room_types()

        # ASSERT
        with backend.work_on("channel.wubook.pms.room.type") as work:
            binder = work.component(usage="binder")
        r1_obtained = binder.to_internal(r1w_id, unwrap=True)

        asserts = [
            lambda: self.assertEqual(
                r1.id,
                r1_obtained.id,
                "The room type existing differs from the one imported",
            ),
            lambda: self.assertCountEqual(
                r1_obtained.pms_property_ids.mapped("id"),
                [p1.id, p2.id],
                "The property of the backend should have been added to room type",
            ),
            lambda: self.assertFalse(
                r1_obtained.company_id, "The company should be null"
            ),
        ]
        for assrt in asserts:
            with self.subTest(assrt):
                assrt()

    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_existing_case04(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type r1 exists
                - r1 has property p1, p2
                - p1, p2 have company m1
                - r1 has company null
                - rb1 binding does not exist
        ACT:    - import r1 from property p4
                - p4 has company m1
        POST:   - new binding rb1 is created
                - rb1 contains existing r1 wrapped
                - r1 has properties p1, p2, p4
                - r1 company is still null
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        m1 = p1.company_id
        p2 = self.env["pms.property"].create(
            {
                "name": "p2",
                "company_id": m1.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )
        p4 = self.env["pms.property"].create(
            {
                "name": "p4",
                "company_id": m1.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )

        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p4.id,
                "user_id": self.user1(p4).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )

        with backend.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")

        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 1,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter.create(r1w_values)

        r1 = self.env["pms.room.type"].create(
            {
                "name": "Room type r1",
                "list_price": 1.0,
                "default_code": "c1",
                "class_id": self.ref("pms.pms_room_type_class_0"),
                "pms_property_ids": [(6, 0, [p1.id, p2.id])],
                "company_id": False,
            }
        )

        # ACT
        backend.import_room_types()

        # ASSERT
        with backend.work_on("channel.wubook.pms.room.type") as work:
            binder = work.component(usage="binder")
        r1_obtained = binder.to_internal(r1w_id, unwrap=True)

        asserts = [
            lambda: self.assertEqual(
                r1.id,
                r1_obtained.id,
                "The room type existing differs from the one imported",
            ),
            lambda: self.assertCountEqual(
                r1_obtained.pms_property_ids.mapped("id"),
                [p1.id, p2.id, p4.id],
                "The property of the backend should have been added to room type",
            ),
            lambda: self.assertFalse(
                r1_obtained.company_id, "The company should be null"
            ),
        ]
        for assrt in asserts:
            with self.subTest(assrt):
                assrt()

    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_existing_case05(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type r1 exists
                - r1 has property p1, p2
                - p1, p2 have company m1
                - r1 has company null
                - r1 has class cl1
                - cl1 exists
                - cl1 has property p1, p2
                - cl1r binding does not exist
                - r1 has 2 bindings rb1 and rb2
                - rb1 is from p1
                - rb2 id from p2
        ACT:    - remove p2
                - import r1 from property p2
                - p2 has company m1
        POST:   - rb1 is bound to r1
                - r1 has properties p1, p2 (p2 is re-added)
                - r1 company is still null
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        m1 = p1.company_id
        p2 = self.env["pms.property"].create(
            {
                "name": "p2",
                "company_id": m1.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )
        backend1 = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend 1",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )
        backend2 = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend 2",
                "pms_property_id": p2.id,
                "user_id": self.user1(p2).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
                "property_code": "X2",
            }
        )

        cl1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room",
                "default_code": "RO",
                "pms_property_ids": [(6, 0, [p1.id, p2.id])],
            }
        )

        with backend1.work_on("channel.wubook.pms.room.type") as work:
            adapter1 = work.component(usage="backend.adapter")
        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 1,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter1.create(r1w_values)

        with backend2.work_on("channel.wubook.pms.room.type") as work:
            adapter2 = work.component(usage="backend.adapter")
        r2w_values = dict(r1w_values)
        r2w_id = adapter2.create(r2w_values)

        # create the bindings
        r1b = self.env["channel.wubook.pms.room.type"].create(
            {
                "name": "Room type r1",
                "list_price": 1.0,
                "default_code": "c1",
                "class_id": cl1.id,
                "pms_property_ids": [(6, 0, [p1.id, p2.id])],
                "company_id": False,
                "backend_id": backend1.id,
            }
        )
        with backend1.work_on("channel.wubook.pms.room.type") as work:
            binder1 = work.component(usage="binder")
            binder1.bind(r1w_id, r1b)
            r1 = binder1.to_internal(r1w_id, unwrap=True)

        r2b = self.env["channel.wubook.pms.room.type"].create(
            {
                "odoo_id": r1.id,
                "backend_id": backend2.id,
            }
        )
        with backend2.work_on("channel.wubook.pms.room.type") as work:
            binder2 = work.component(usage="binder")
            binder2.bind(r2w_id, r2b)

        # ACT
        r1.pms_property_ids = [(3, p2.id, 0)]
        backend2.import_room_types()

        # ASSERT
        self.assertCountEqual(
            r1.pms_property_ids.ids,
            [p1.id, p2.id],
            "The binding does not contain the two original properties",
        )

    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_existing_case06(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type r1 exists
                - r1 has property p1, p2
                - p1, p2 have company m1
                - r1 has company null
                - rb1 and rb2 bindings exist
        ACT:    - remove p1 and p2
                - import r1 from property p1
                - p1 has company m1
                - import r1 from property p2
                - p2 has company m1
        POST:   - rb1 is bound to r1
                - r1 has no properties
                - r1 company is still null
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        m1 = p1.company_id
        p2 = self.env["pms.property"].create(
            {
                "name": "p2",
                "company_id": m1.id,
                "default_pricelist_id": self.ref("product.list0"),
            }
        )
        backend1 = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend 1",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )
        backend2 = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend 2",
                "pms_property_id": p2.id,
                "user_id": self.user1(p2).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
                "property_code": "X2",
            }
        )
        with backend1.work_on("channel.wubook.pms.room.type") as work:
            adapter1 = work.component(usage="backend.adapter")
        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 2,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter1.create(r1w_values)

        with backend2.work_on("channel.wubook.pms.room.type") as work:
            adapter2 = work.component(usage="backend.adapter")
        r2w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 2,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r2w_id = adapter2.create(r2w_values)

        # create the bindings
        r1b = self.env["channel.wubook.pms.room.type"].create(
            {
                "name": "Room type r1",
                "list_price": 1.0,
                "default_code": "c1",
                "class_id": self.ref("pms.pms_room_type_class_0"),
                "pms_property_ids": [(6, 0, [p1.id, p2.id])],
                "company_id": False,
                "backend_id": backend1.id,
            }
        )
        with backend1.work_on("channel.wubook.pms.room.type") as work:
            binder1 = work.component(usage="binder")
            binder1.bind(r1w_id, r1b)
            r1 = binder1.to_internal(r1w_id, unwrap=True)

        r2b = self.env["channel.wubook.pms.room.type"].create(
            {
                "odoo_id": r1.id,
                "backend_id": backend2.id,
            }
        )
        with backend2.work_on("channel.wubook.pms.room.type") as work:
            binder2 = work.component(usage="binder")
            binder2.bind(r2w_id, r2b)

        # ACT
        r1.pms_property_ids = [(3, p1.id, 0), (3, p2.id, 0)]
        backend1.import_room_types()
        backend2.import_room_types()

        # ASSERT
        self.assertFalse(
            r1.pms_property_ids,
            "The binding still contains properties",
        )


class TestWubookConnectorRoomTypeExport(common.TestWubookConnector):
    @mock.patch.object(xmlrpc.client, "Server")
    def test_export_existing_case01(self, mock_xmlrpc_client_server):
        """
        PRE:    - r1 exists
                - r1 has code 'c1'
                - r1 has property p1
                    - p1 has company m1
                - r1 has no company defined
                - r1 has no binding
                - on the backend exists a record with shortname 'c1'
                - r1w has different name and price than r1
        ACT:    - export all rooms (only r1 exists)
        POST:   - r1 has binding r1b
                - r1b has the same external_id as the id the record
                  on the backend
                - r1b additional fields min_price, max_price are created
                  with the values of the backend
                - r1 fields as list_price is not imported from the backend and
                  it kepts the original value
                - r1w has the same name and price than r1
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")

        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )
        with backend.work_on("channel.wubook.pms.room.type") as work:
            binding_model = work.model
            adapter = work.component(usage="backend.adapter")
            binder = work.component(usage="binder")

        bs1 = self.env["pms.board.service"].create(
            {
                "name": "All included",
                "default_code": "AI",
                "board_service_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "pms.pms_service_0_product_template"
                            ).id,
                        },
                    )
                ],
            }
        )
        r1_values = {
            "name": "Room type r1",
            "list_price": 30.0,
            "default_code": "c1",
            "class_id": self.env.ref("pms.pms_room_type_class_0").id,
            "pms_property_ids": [(6, 0, [p1.id])],
            "board_service_room_type_ids": [
                (
                    0,
                    0,
                    {
                        "pms_board_service_id": bs1.id,
                    },
                )
            ],
            "company_id": False,
        }
        r1 = self.env["pms.room.type"].create(r1_values)

        r1w_values = {
            "name": "Room type Diff",
            "shortname": "c1",
            "rtype": 2,
            "min_price": 5.0,
            "max_price": 200.0,
            "price": 66,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter.create(r1w_values)

        # ACT
        binding_model.export_batch(backend_record=backend, domain=[("id", "=", r1.id)])

        # ASSERT
        r1b = binder.wrap_record(r1)

        with self.subTest():
            self.assertTrue(
                bool(binder.unwrap_binding(r1b)), "The binding should exist"
            )
        with self.subTest():
            self.assertEqual(
                binder.unwrap_binding(r1b).id,
                r1.id,
                "The binding exists but the id of the real record should match",
            )
        with self.subTest():
            self.assertEqual(
                r1b.external_id,
                r1w_id,
                "The external id's should be the same on the binding "
                "and on the backend ",
            )
        with self.subTest():
            self.assertEqual(
                [r1b.min_price, r1b.max_price],
                [r1w_values["min_price"], r1w_values["max_price"]],
                "The additional fields have not been imported to binding",
            )
        with self.subTest():
            self.assertEqual(
                r1.list_price,
                r1_values["list_price"],
                "The price belongs to the real record and not the binding, "
                "so it shouldn't be changed",
            )
        with self.subTest():
            r1w_new = adapter.search_read([("id", "=", r1w_id)])[0]
            self.assertEqual(
                [r1.name, r1.list_price],
                [r1w_new["name"], r1w_new["price"]],
                "The price and the name were not exported",
            )

    @mock.patch.object(xmlrpc.client, "Server")
    def test_export_existing_case02(self, mock_xmlrpc_client_server):
        """
        PRE:    - r1 exists
                - r1 has code 'c1'
                - r1 has property p1
                    - p1 has company m1
                - r1 has no company defined
                - r1 has binding r1b
                - r1b has no external_id
                - r1w exists on the backend
                - r1w has different name and price than r1
        ACT:    - export all rooms (only r1 exists)
        POST:   - r1 still has a binding
                - r1 has r1b binding (the same as before)
                - the odoo record linked to r1b is still the same as before
                - r1b has external_id and is the id of the external record
                - r1b additional fields min_price, max_price are not imported
                  and they kept their original value because the binding
                  exists eventhough it has not external_id
                - r1 fields as list_price is not imported from the backend and
                  it kepts the original value
                - r1w has the same name and price than r1
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )
        with backend.work_on("channel.wubook.pms.room.type") as work:
            binding_model = work.model
            adapter = work.component(usage="backend.adapter")
            binder = work.component(usage="binder")

        r1_values = {
            "name": "Room type r1",
            "list_price": 30.0,
            "default_code": "c1",
            "class_id": self.ref("pms.pms_room_type_class_0"),
            "pms_property_ids": [(6, 0, [p1.id])],
            "company_id": False,
        }
        r1 = self.env["pms.room.type"].create(r1_values)
        r1b = binder.wrap_record(r1, force=True)
        r1b_values = {
            "min_price": 11.0,
            "max_price": 21.0,
        }
        r1b.write(r1b_values)

        r1w_values = {
            "name": "Room type Diff",
            "shortname": "c1",
            "rtype": 2,
            "min_price": 5.0,
            "max_price": 200.0,
            "price": 66.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
        }
        r1w_id = adapter.create(r1w_values)

        # ACT
        binding_model.export_batch(backend_record=backend, domain=[("id", "=", r1.id)])

        # ASSERT
        r1b_new = binder.wrap_record(r1)

        with self.subTest():
            self.assertTrue(
                bool(binder.unwrap_binding(r1b_new)), "The binding should exist"
            )
        with self.subTest():
            self.assertEqual(
                r1b.id,
                r1b_new.id,
                "The binding should be the same as the one before export",
            )
        with self.subTest():
            self.assertEqual(
                r1.id,
                binder.unwrap_binding(r1b_new).id,
                "The id of the real record on the binding does not match",
            )
        with self.subTest():
            self.assertEqual(
                r1b_new.external_id,
                r1w_id,
                "The external id's should be the same on the binding "
                "and on the backend ",
            )
        with self.subTest():
            self.assertEqual(
                [r1b_new.min_price, r1b_new.max_price],
                [r1b_values["min_price"], r1b_values["max_price"]],
                "The additional fields have been imported to binding "
                "and it shouldn't have happened",
            )
        with self.subTest():
            r1w_new = adapter.search_read([("id", "=", r1w_id)])[0]
            self.assertEqual(
                [r1.name, r1.list_price],
                [r1w_new["name"], r1w_new["price"]],
                "The price and the name were not exported",
            )


# @tagged("test_debug")
class TestWubookConnectorRoomTypeReuseBinding(common.TestWubookConnector):
    # existing
    @mock.patch.object(xmlrpc.client, "Server")
    def test_export_reuse_binding_case01(self, mock_xmlrpc_client_server):
        """
        PRE:    - r1 exists
                - r1 has code 'c1'
                - r1 has no binding
                - on the backend exists a record with shortname 'c1'
        ACT:    - export r1
        POST:   - r1 has binding r1b
                - r1b has the same external_id as the id the record
                  on the backend
                - r1b additional fields min_price, max_price are created
                  with the values of the backend
                - r1 fields as list_price is not imported from the backend and
                  it kepts the original value
        :return:
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )

        with backend.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")
        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 2,
            "price": 100.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
            "min_price": 5,
            "max_price": 200,
        }
        # r1w_id
        adapter.create(r1w_values)

        r1_values = {
            "name": "Room type r1",
            "list_price": 30,
            "default_code": "c1",
            "class_id": self.ref("pms.pms_room_type_class_0"),
            "pms_property_ids": [(6, 0, [self.ref("pms.main_pms_property")])],
            "company_id": False,
        }
        r1 = self.env["pms.room.type"].create(r1_values)

        with backend.work_on("channel.wubook.pms.room.type") as work:
            binder = work.component(usage="binder")

        # ACT
        r1b = binder.to_binding_from_internal_key(r1)

        # ASSERT
        asserts = [
            (
                binder.unwrap_binding(r1b),
                r1,
                "The binding does not belong to real record",
            ),
            (
                binder.to_external(r1, wrap=True),
                r1b.external_id,
                "The external id is not the same on both binding and real",
            ),
            (
                [getattr(r1b, x) for x in ["max_price", "min_price"]],
                [r1w_values[x] for x in ["max_price", "min_price"]],
                "The additional fields have not been imported to binding",
            ),
            (
                r1b.list_price,
                r1_values["list_price"],
                "The price belongs to the real record and not the binding, "
                "so it shouldn't be changed",
            ),
        ]
        for assrt in asserts:
            with self.subTest():
                self.assertEqual(*assrt)

    @mock.patch.object(xmlrpc.client, "Server")
    def test_export_reuse_binding_case02(self, mock_xmlrpc_client_server):
        """
        PRE:    - r1 exists
                - r1 has code 'c1'
                - r1 has binding r1b
                - r1b has no external_id
                - on the backend exists a record with shortname 'c1'
        ACT:    - export r1
        POST:   - r1 still has binding r1b and is the same
                - r1b has external_id and is the id of the external record
                - r1b additional fields min_price, max_price are created
                  with the values of the backend
                - r1 fields as list_price is not imported from the backend and
                  it kepts the original value
        :return:
        """
        # mock object
        mock_server = server.MockWubookServer()
        mock_xmlrpc_client_server.return_value = mock_server.get_mock()

        # ARRANGE
        p1 = self.browse_ref("pms.main_pms_property")
        backend = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "pms_property_id": p1.id,
                "user_id": self.user1(p1).id,
                "backend_type_id": self.backend_type1.parent_id.id,
                **self.fake_credentials,
            }
        )

        with backend.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")
        r1w_values = {
            "name": "Room type r1",
            "shortname": "c1",
            "rtype": 2,
            "price": 1.0,
            "availability": 2,
            "board": "ai",
            "occupancy": 6,
            "woodoo": 0,
            "min_price": 5.0,
            "max_price": 200.0,
        }
        r1w_id = adapter.create(r1w_values)

        r1_values = {
            "name": "Room type r1",
            "list_price": 30,
            "default_code": "c1",
            "class_id": self.ref("pms.pms_room_type_class_0"),
            "pms_property_ids": [(6, 0, [self.ref("pms.main_pms_property")])],
            "company_id": False,
        }
        r1 = self.env["pms.room.type"].create(r1_values)

        r1b0 = self.env["channel.wubook.pms.room.type"].create(
            {
                "odoo_id": r1.id,
                "backend_id": backend.id,
            }
        )

        with backend.work_on("channel.wubook.pms.room.type") as work:
            binder = work.component(usage="binder")

        # ACT
        r1b = binder.to_binding_from_internal_key(r1)

        # ASSERT
        asserts = [
            (
                r1b.id,
                r1b0.id,
                "The binding has changed it should be the same only updated",
            ),
            (r1b.external_id, r1w_id, "The external id is not the one on the backend"),
            (
                [getattr(r1b, x) for x in ["max_price", "min_price"]],
                [r1w_values[x] for x in ["max_price", "min_price"]],
                "The additional fields have not been imported to binding",
            ),
            (
                r1b.list_price,
                r1_values["list_price"],
                "The price belongs to the real record and not the binding, "
                "so it shouldn't be changed",
            ),
        ]
        for assrt in asserts:
            with self.subTest():
                self.assertEqual(*assrt)


# TODO: add this mock test and add more cases
# @tagged("test_debug")
# class TestServerMock(common.TestWubookConnector):
#     @mock.patch.object(xmlrpc.client, "Server")
#     def test_create_room_case01(self, mock_xmlrpc_client_server):
#         # mock object
#         mock_server = server.MockWubookServer()
#         mock_xmlrpc_client_server.return_value = mock_server.get_mock()
#
#         # ARRANGE
#         p1 = self.browse_ref("pms.main_pms_property")
#
#         backend = self.env["channel.wubook.backend"].create(
#             {
#                 "name": "Test backend 1",
#                 "pms_property_id": p1.id,
#                 "model_id": self.ref(
#                     "connector_pms_wubook.model_channel_wubook_backend"
#                 ),
#                 "username": "X",
#                 "password": "X",
#                 "property_code": "X",
#                 "pkey": "X",
#             }
#         )
#
#         with backend.work_on("channel.wubook.pms.room.type") as work:
#             adapter = work.component(usage="backend.adapter")
#
#         r1w ={
#                 "woodoo": 0,
#                 "name": "Room type r1",
#                 "occupancy": 2,
#                 "price": 100,
#                 "availability": 1,
#                 "shortname": "c1",
#                 "board": 'nb',
#                 "min_price": 5,
#                 "max_price": 200,
#             }
#
#         r = adapter.create(r1w)
#         print(r)
#         return
#         u = adapter.search_read([])
#         print(u)
#
#         u = adapter.search([])
#         print(u)
#
#         return
#         r1w['shortname'] = 'c2'
#         r = adapter.create(r1w)
#         print(r)
#
#         r = adapter.search_read([])
#         print(r)
#
#         r = adapter.search([])
#         print(r)
#
#         r1w_values = dict(r1w)
#         r1w_values['name']="CHANGED!!!"
#         r = adapter.write(1, r1w_values)
#
#         r = adapter.search([])
#
#         r = adapter.search_read([('id', '=', 1)])
#         print("sear", r)

# @tagged('test_debug')
# class TestRT(common.TestWubookConnector):
#     pass
