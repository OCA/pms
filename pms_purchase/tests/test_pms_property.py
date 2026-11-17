# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import common


class TestPmsProperty(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.pms_property_model = self.env["pms.property"]

    def _create_product(self, name):
        return self.env["product.product"].create(
            {
                "name": name,
                "type": "consu",
                "is_storable": True,
                "purchase_ok": True,
            }
        )

    def test_pms_property_generate(self):
        partner_a = self.env["res.partner"].create(
            {
                "name": "test email 1",
                "email": "test1@example.com",
            }
        )

        pms_property_obj = self.env["pms.property"]

        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )

        pms_property_vals = {
            "name": "Test Pms Property-1",
            "owner_id": partner_a.id,
            "stock_location_id": self.env.ref("stock.stock_location_stock").id,
        }
        pms_property_record = pms_property_obj.create(pms_property_vals)

        PurchaseOrder = self.env["purchase.order"].with_context(tracking_disable=True)
        company = self.env.user.company_id
        product_1 = self._create_product("Purchase Test Product 1")
        product_2 = self._create_product("Purchase Test Product 2")

        picking_type = self.env["stock.picking.type"].create(
            {
                "name": "new_picking_type",
                "code": "outgoing",
                "sequence_code": "NPT",
                "default_location_src_id": self.env.ref(
                    "stock.stock_location_suppliers"
                ).id,
                "default_location_dest_id": self.env.ref(
                    "stock.stock_location_stock"
                ).id,
                "warehouse_id": warehouse.id,
            }
        )

        vals = {
            "partner_id": partner_a.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "picking_type_id": picking_type.id,
            "date_order": "2019-01-01",
            "order_line": [
                Command.create(
                    {
                        "product_id": product_1.id,
                    },
                )
            ],
        }
        purchase_order = PurchaseOrder.create(vals)

        # The property analytic distribution is set by the compute, so it also
        # applies to RPC and import, which never run onchanges.
        purchase_order.order_line.write({"pms_property_id": pms_property_record.id})

        self.assertEqual(pms_property_record.po_line_count_calculated, 1)
        action = pms_property_record.action_open_po_line()
        self.assertEqual(
            action["domain"], [("id", "in", purchase_order.order_line.ids)]
        )
        self.assertEqual(
            purchase_order.order_line.analytic_distribution,
            {str(pms_property_record.analytic_id.id): 100},
        )

        self.env["stock.putaway.rule"].create(
            {
                "product_id": product_2.id,
                "location_in_id": self.env.ref("stock.stock_location_stock").id,
                "move_to_property": True,
                "location_out_id": self.env.ref("stock.stock_location_suppliers").id,
            }
        )

        purchase_order.write(
            {
                "order_line": [
                    Command.create(
                        {
                            "product_id": product_2.id,
                            "pms_property_id": pms_property_record.id,
                        },
                    )
                ]
            }
        )
        pms_property_record.action_open_po_line()
        purchase_order.button_confirm()
