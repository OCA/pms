# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

from odoo.tests.common import tagged

from . import common

_logger = logging.getLogger(__name__)


@tagged("test_debug")
class TestPmsAvailabilityPlan(common.TestWubookConnector):
    def test_availability_plan_01(self):
        # ARRANGE
        property1 = self.browse_ref("pms.main_pms_property")

        backend1 = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "user_id": self.user1(property1).id,
                "pms_property_id": property1.id,
                "backend_type_id": self.backend_type1.parent_id.id,
                "pricelist_external_id": 1,
                # **self.fake_credentials,
                **self.test_credentials,
            }
        )

        with backend1.work_on("channel.wubook.pms.room.type") as work:
            adapter = work.component(usage="backend.adapter")

        avail_values = adapter._exec("get_channels_info", pms_property=False)
        print(avail_values)

        return

        with backend1.work_on("channel.wubook.pms.availability.plan") as work:
            adapter = work.component(usage="backend.adapter")

        # values = adapter._exec("rplan_rplans")
        # print(values)

        values = adapter.search_read(
            [
                ("date", ">", datetime.date(2021, 7, 1)),
                ("date", "<", datetime.date(2021, 7, 7)),
            ]
        )
        print("------", values)

        return

        # with backend1.work_on("channel.wubook.pms.room.type") as work:
        #     adapter = work.component(usage="backend.adapter")
        #
        # avail_values = adapter._exec("get_channels_info", pms_property=False)
        # print(avail_values)
        #
        # return

        with backend1.work_on("channel.wubook.pms.folio") as work:
            adapter = work.component(usage="backend.adapter")

        values = adapter.read("1624299403")
        print("---------", values)

        return

        plan = self.env["pms.availability.plan"].search([("name", "=", "Plan1")])
        room = self.env["pms.room.type"].search([("default_code", "=", "QUIN")])

        self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": plan.id,
                "room_type_id": room.id,
                "pms_property_id": property1.id,
                "date": datetime.date(2020, 6, 25),
            }
        )

        return

        # with backend1.work_on("channel.wubook.pms.room.type") as work:
        #     adapter = work.component(usage="backend.adapter")
        #
        # avail_values = adapter._exec("get_channels_info")
        # print(avail_values)
        #
        # return
        # with backend1.work_on("channel.wubook.pms.room.type") as work:
        #     adapter = work.component(usage="backend.adapter")
        #
        # # res = adapter.search_read([
        # #     ('shortname', '=', 'c1')
        # # ])
        # rooms = [478465, 478468, 478469, 478470, 478471, 478473, 478474, 478477, 501774, 478478, 478480, 477968, 501773,
        #   478485, 478486, 478487, 478488, 478489, 510620, 510621, 510622, 510624, 510625, 510626, 503764, 478434,
        #   478435, 478437, 478457, 478460, 478461]
        # kw_params = {
        #     'date_from': '18/06/2021',
        #     'date_to': '16/06/2021',
        #     #"rooms": list(rooms),
        # }
        # params = adapter._prepare_parameters(
        #     kw_params, ["date_from", "date_to"], ["rooms"]
        # )
        # avail_values = adapter._exec("fetch_rooms_values", *params)
        #
        #
        #
        # print("***", avail_values)
        # return
        # res = adapter.write(503764, {
        #     'name': 'Room type r1',
        #     'occupancy': 6,
        #     'price': 11.0,
        #     "availability": 2,
        #     "shortname": 'c1',
        #     'board': 'ai',
        #     #############
        #     "names": False,
        #     "descriptions": False,
        #     #"boards": {'nb': {'dtype': 2, 'value': 0}},
        #     "boards": {},
        #     "min_price": False,
        #     "max_price": False,
        #     "rtype": 2,
        #     "woodoo": 0,
        # })
        #
        # print("***", res)
        #
        # return

        # with backend1.work_on("channel.wubook.pms.availability.plan") as work:
        #     adapter = work.component(usage="backend.adapter")
        #
        # res = adapter.search_read(
        #     [
        #         ("name", "in", ("test95K", "test90K", "test119", "test109", "test101", "test8", "test4")),
        #         ("date", ">", datetime.datetime(2021, 6, 1)),
        #         ("date", "<", datetime.datetime(2021, 6, 5)),
        #         # ('id_room', 'in', [503764]),
        #         # ('dfrom', '=', datetime.datetime(2021, 6, 1)),
        #         # ('dto', '=', datetime.datetime(2021, 6, 5))
        #     ]
        # )
        # print("**************", res, len(res)) #, len(res))

        # backend1.plan_date_from = datetime.date(2021, 6, 3)
        # backend1.plan_date_to = datetime.date(2021, 6, 10)
        # # backend1.plan_room_type_ids = False
        #
        # backend1.import_availability_plans()

        # backend1.export_availability_plans()
        # backend1.export_room_types()
        backend1.import_room_types()

        return
