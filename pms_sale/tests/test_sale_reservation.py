# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestSaleReservation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref("pms_sale.product_product_reservation")
        cls.partner_owner = cls.env["res.partner"].create({"name": "Property Owner"})
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.property = cls.env["pms.property"].create(
            {
                "name": "Test Property",
                "owner_id": cls.partner_owner.id,
                "no_of_guests": 4,
                "min_nights": 1,
                "max_nights": 30,
            }
        )
        cls.reservation_type = cls.env["pms.property.reservation"].create(
            {
                "name": "Test Reservation Type",
                "product_id": cls.product.id,
                "property_id": cls.property.id,
            }
        )
        today = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        cls.start = today + timedelta(days=10)
        cls.stop = today + timedelta(days=15)

    def _make_reservation(self):
        return self.env["pms.reservation"].create(
            {
                "property_id": self.property.id,
                "start": self.start,
                "stop": self.stop,
                "partner_id": self.partner.id,
                "no_of_guests": 2,
            }
        )

    def test_sale_order_line_links_reservation(self):
        """SOL with pms_reservation_id links order info back to the reservation."""
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        reservation = self._make_reservation()
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "pms_reservation_id": reservation.id,
            }
        )
        self.assertEqual(reservation.sale_order_id, order)
        self.assertEqual(reservation.sale_order_line_id, line)
        self.assertEqual(reservation.property_id, self.property)

    def test_confirm_sale_order(self):
        """Confirming a sale order with a reservation line sets state to 'sale'."""
        reservation = self._make_reservation()
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "pms_reservation_id": reservation.id,
                        },
                    )
                ],
            }
        )
        self.assertEqual(order.state, "draft")
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertEqual(order.order_line.pms_reservation_id, reservation)
        self.assertEqual(reservation.sale_order_id, order)

    def test_cancel_line_cancels_reservation(self):
        """Unlinking a sale order line cancels its linked pms.reservation."""
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        reservation = self._make_reservation()
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "pms_reservation_id": reservation.id,
            }
        )
        stage_cancelled = self.env.ref(
            "pms_sale.pms_stage_cancelled", raise_if_not_found=False
        )
        line.unlink()
        self.assertEqual(reservation.stage_id, stage_cancelled)
