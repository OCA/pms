# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.tests import common


class TestPmsProperty(common.TransactionCase):
    def setUp(self):
        super(TestPmsProperty, self).setUp()

        # Get required Model
        self.pms_property_model = self.env["pms.property"]

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
                (
                    0,
                    0,
                    {
                        "product_id": self.env.ref("product.product_delivery_01").id,
                        "pms_property_id": pms_property_record.id,
                    },
                )
            ],
        }
        purchase_order = PurchaseOrder.create(vals)
        purchase_order.order_line._onchange_pms_property_id()

        pms_property_record._compute_po_line_count()
        pms_property_record.action_open_po_line()

        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.env.ref("product.product_delivery_02").id,
                "location_in_id": self.env.ref("stock.stock_location_stock").id,
                "method": "move_to_property",
                "location_out_id": self.env.ref("stock.stock_location_suppliers").id,
            }
        )

        purchase_order.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "pms_property_id": pms_property_record.id,
                        },
                    )
                ]
            }
        )
        pms_property_record.action_open_po_line()
        purchase_order.button_confirm()
