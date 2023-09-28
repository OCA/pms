# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from . import common

_logger = logging.getLogger(__name__)


# @tagged("test_debug")
class TestWubookConnectorProductPricelist(common.TestWubookConnector):
    def test_product_pricelist_01(self):
        # ARRANGE
        property1 = self.browse_ref("pms.main_pms_property")

        backend1 = self.env["channel.wubook.backend"].create(
            {
                "name": "Test backend",
                "user_id": self.user1(property1).id,
                "pms_property_id": property1.id,
                "backend_type_id": self.backend_type1.parent_id.id,
                # **self.fake_credentials,
                **self.test_credentials,
            }
        )

        # -----------------------------------

        # ---------------------------------------------

        # with backend.work_on("channel.wubook.product.pricelist") as work:
        #     binding_model = work.model
        #
        # binding_model.import_batch(backend, domain=[('name', '=', 'vtest68')])
        #
        # binding_model.import_batch(backend, domain=[('name', '=', 'vtest68')])
        #
        # pl = self.env["channel.wubook.product.pricelist"].search([])
        # for i in pl:
        #     print(i)
        #
        # a = 1
        #
        # return

        # ---------------------------------------------

        # parent = self.env["channel.wubook.product.pricelist"].create({
        #     'name': 'child',
        #     'backend_id': backend.id,
        # })
        # print("222222222222222 --------------", parent, parent.name)
        #
        # parent.write({
        #     'name': 'pepe',
        #     'item_ids': [(0, 0, {
        #         'applied_on': '3_global',
        #         'compute_price': 'formula',
        #         # 'base': 'pricelist',
        #         # 'base_pricelist_id': parent.odoo_id.id,
        #         # 'price_discount': 69,
        #         # 'pricelist_id': child.odoo_id.id,
        #     })]
        # })
        # print("333333333333333333 --------------------", parent, parent.name,
        #       parent.item_ids, parent.item_ids.compute_price,
        #       parent.item_ids.pricelist_id.name)
        #
        # # child.write({
        # #     'name': 'uu',
        # # })
        # parent.write({
        #     'name': 'uu',
        #     'sequence': 66,
        #     'item_ids': [
        #         (1, parent.item_ids.id, {
        #             'applied_on': '3_global',
        #             'compute_price': 'fixed',
        #             # 'base': 'pricelist',
        #             # 'base_pricelist_id': parent.odoo_id.id,
        #             # 'price_discount': 88,
        #             # 'pricelist_id': child.odoo_id.id,
        #         })]
        # })
        # print("4444444444444444 --------------", parent, parent.name, parent.item_ids,
        #       parent.item_ids.compute_price,
        #       parent.item_ids.pricelist_id.name, parent.sequence)
        #
        # return

        # with backend.work_on("channel.wubook.pms.room.type") as work:
        #     adapter = work.component(usage="backend.adapter")
        #     print(adapter.search_read([('shortname', '=', 'H217')]))

        # with backend.work_on("channel.wubook.product.pricelist") as work:
        #     adapter = work.component(usage="backend.adapter")
        #     print("----------------__", adapter)
        # # res = adapter.create({'name': 'TEST55'})
        # res = adapter.search_read([])
        # print("**", res)
        # res = adapter.search_read([('id', '=', 178429)])
        # res = adapter.search_read([('id', 'in', [178429, 178424,178428,])])
        # res = adapter.search_read([('name', '=', 'TEST55')])
        # res = adapter.search_read([
        #     #('id', 'in', [178429, 178424, 178428]),
        #     #('dfrom', '=', datetime.date(2021, 2, 1)),
        #     #('dto', '=', datetime.date(2021, 2, 2)),
        #     #('rooms', 'in', [478457, 478459]),
        #     # ('pl', '=', 6565)
        #     ('vpid', '=', 178428)
        # ])
        # res = adapter.read(178428)
        # print("******", res)

        # res = adapter.write(178538, {
        #     'name': 'vT445',
        #     'items': [{
        #         'type': 'pricelist',
        #         'variation': 11,
        #         'variation_type': 2
        #     }]
        # })
        # print("************", res)

        # test de rooms
        # res = adapter.write(
        #     178538,
        #     {
        #         "name": "vT445",
        #         "items": [
        #             {"type": "virtual", "variation": 11, "variation_type": 2}
        #         ],
        #     },
        # )
        # print("************", res)
        #
        # res = adapter.search_read([("id", "=", 178538)])
        # print("******", res)

        # res = adapter.create({
        #     'name': 'T445',
        #     'items': [{
        #         'type': 'pricelist',
        #         'variation': 10,
        #         'variation_type': -1,
        #     }]
        # })
        # print("******", res)

        # res = adapter.search_read([])
        # print("**", res)
        #
        # res = adapter.write(178428, {
        #     'variation': 66,
        #     'variation_type': -1
        # })
        # print("**", res)
        #
        #
        # res = adapter.search_read([])
        # print("**", res)
        # res = adapter.delete(177581)
        # print(res)
        # res = adapter.search_read([('name', '=', 'TEST55'), ('vpid', '!=', False)])
        # print("**", res)
        # res = adapter.write(178427, {'name':'test11'})
        # print("**", res)
        # res = adapter.write(178429, {
        #     'rack': {str(477968): [63, 64, 65, 66, 67, 68, 69]}
        # })
        # res = adapter.write(178429, {
        #     'rack': {str(477968): [63, 64, 65, 66, 67, 68, 69]}
        # })
        # res = adapter.write(178427, {'name':'test11'})
        # print("**", res)

        # res = adapter.search_read([])
        # print("**", res)

        # with backend.work_on("channel.wubook.product.pricelist.item") as work:
        #     adapter = work.component(usage="backend.adapter")
        #
        # # res = adapter.search_read([])
        #
        # dfrom = datetime.datetime(2021, 1, 1)
        # dto = datetime.datetime(2021, 2, 8)
        # res = adapter.search_read([
        #     ('vpid', '=', 178429), # real
        #     #('vpid', '=', 178428), # virtual
        #     ('dfrom', '=', dfrom),
        #     ('dto', '=', dto),
        #     ('rooms', 'in', [478457, 478459]),
        #     #('pl', '=', 6565)
        # ])
        # print("*", res)

        backend1.export_availability_plans()
        backend1.export_room_types()

        return
