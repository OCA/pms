# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
import xmlrpc.client

import mock

from . import common, server

_logger = logging.getLogger(__name__)


# @tagged('test_debug')
class TestWubookConnectorRoomTypeClassImport(common.TestWubookConnector):
    # non-existing
    @mock.patch.object(xmlrpc.client, "Server")
    def test_import_non_existing_case01(self, mock_xmlrpc_client_server):
        """
        PRE:    - room type class cl1 does not exist
        ACT:    - import cl1 from property p1
        POST:   - room type class cl1 imported
                - cl1 has the values from the backend
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

        cl1w_values = {
            "name": "Apartment",
        }
        cl1w_id = 2

        # ACT
        backend.import_room_type_classes()

        # ASSERT
        with backend.work_on("channel.wubook.pms.room.type.class") as work:
            binder = work.component(usage="binder")
        cl1 = binder.to_internal(cl1w_id, unwrap=True)

        mapped_fields = [
            ("name", "name"),
        ]
        odoo_values = [getattr(cl1, x) for _, x in mapped_fields] + [
            cl1.pms_property_ids
        ]
        wubook_values = [cl1w_values.get(x) for x, _ in mapped_fields] + [
            backend.pms_property_id
        ]

        self.assertListEqual(
            odoo_values,
            wubook_values,
            "The room type class data on Odoo does not match the data on Wubook",
        )
