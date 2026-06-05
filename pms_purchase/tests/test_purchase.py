# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.tests import common


class TestPurchase(common.TransactionCase):
    def test_purchase_order_generate(self):
        PurchaseOrder = self.env["purchase.order"].with_context(tracking_disable=True)

        partner_a = self.env["res.partner"].create(
            {
                "name": "test email 1",
                "email": "test1@example.com",
            }
        )

        company = self.env.user.company_id

        self.env["ir.sequence"].search([("code", "=", "purchase.order")]).write(
            {
                "use_date_range": True,
                "prefix": "PO/%(range_year)s/",
            }
        )

        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )

        location_1 = self.env["stock.location"].create(
            {"name": "loc1", "location_id": warehouse.id}
        )

        picking_type = self.env["stock.picking.type"].create(
            {
                "name": "new_picking_type",
                "code": "outgoing",
                "sequence_code": "NPT",
                "default_location_src_id": self.env.ref(
                    "stock.stock_location_stock"
                ).id,
                "default_location_dest_id": location_1.id,
                "warehouse_id": warehouse.id,
            }
        )

        vals = {
            "partner_id": partner_a.id,
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "picking_type_id": picking_type.id,
            "date_order": "2019-01-01",
        }
        purchase_order = PurchaseOrder.create(vals.copy())
        self.assertTrue(purchase_order.name.startswith("PO/2019/"))
        vals["date_order"] = "2020-01-01"
