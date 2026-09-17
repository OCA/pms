# Copyright (c) 2026 ParlonsWeb
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestPMSConfigurator(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref("pms_sale.product_product_reservation")
        cls.partner_owner = cls.env["res.partner"].create({"name": "Property Owner"})
        cls.property = cls.env["pms.property"].create(
            {
                "name": "Property",
                "owner_id": cls.partner_owner.id,
                "no_of_guests": 4,
                "min_nights": 1,
                "max_nights": 30,
            }
        )
        cls.order_customer = cls.env["res.partner"].create({"name": "Order Customer"})
        cls.reservation_customer = cls.env["res.partner"].create(
            {"name": "Reservation Customer"}
        )
        cls.reservation = cls.env["pms.reservation"].create(
            {
                "property_id": cls.property.id,
                "start": "2026-11-10 16:00:00",
                "stop": "2026-11-13 10:00:00",
                "partner_id": cls.reservation_customer.id,
            }
        )

    def test_new_reservation_defaults_partner_from_web_partner_id(self):
        """The Sale Order -> Configurator flow forwards the order's customer
        as web_partner_id context - it should default "Booked by" too, not
        only pre-fill a guest row.
        """
        configurator = self.env["pms.configurator"].with_context(
            web_partner_id=self.order_customer.id
        )
        result = configurator.default_get(["partner_id"])
        self.assertEqual(result.get("partner_id"), self.order_customer.id)

    def test_existing_reservation_defaults_partner_from_reservation(self):
        """Editing an already-linked reservation should keep showing its own
        partner_id, not silently switch it to the order's current customer.
        """
        configurator = self.env["pms.configurator"].with_context(
            default_existing_reservation_id=self.reservation.id,
            web_partner_id=self.order_customer.id,
        )
        result = configurator.default_get(["partner_id"])
        self.assertEqual(result.get("partner_id"), self.reservation_customer.id)

    def test_no_partner_context_leaves_it_unset(self):
        configurator = self.env["pms.configurator"]
        result = configurator.default_get(["partner_id"])
        self.assertFalse(result.get("partner_id"))
