import datetime

from freezegun import freeze_time

from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from .common import TestPms

freeze_time("2000-02-02")


@tagged("post_install", "-at_install")
class TestPmsPayment(TestPms, AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].browse(1)
        cls.env = cls.env(user=cls.user)
        cls.room_type = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
                "list_price": 25,
            }
        )
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Room 101",
                "room_type_id": cls.room_type.id,
                "capacity": 2,
            }
        )
        cls.sale_channel = cls.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
        # Bank journal for the property
        cls.bank_journal = cls.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                "|",
                ("pms_property_ids", "in", cls.pms_property1.id),
                "&",
                ("pms_property_ids", "=", False),
                ("company_id", "=", cls.pms_property1.company_id.id),
            ],
            limit=1,
        )
        if not cls.bank_journal:
            cls.bank_journal = cls.env["account.journal"].create(
                {
                    "name": "Test Bank",
                    "type": "bank",
                    "code": "TBNK",
                    "company_id": cls.pms_property1.company_id.id,
                }
            )
        # Ensure all inbound lines are allowed on PMS
        cls.bank_journal.inbound_payment_method_line_ids.allowed_on_pms = True

    def _create_folio_with_reservation(self):
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "checkin": datetime.date(2000, 2, 2),
                "checkout": datetime.date(2000, 2, 4),
                "partner_name": "Test Partner",
                "sale_channel_origin_id": self.sale_channel.id,
                "room_type_id": self.room_type.id,
            }
        )
        return reservation.folio_id

    # =========================================================================
    # _get_payment_methods tests
    # =========================================================================

    def test_get_payment_methods_returns_method_lines(self):
        """_get_payment_methods returns account.payment.method.line records."""
        result = self.pms_property1._get_payment_methods()
        self.assertEqual(
            result._name,
            "account.payment.method.line",
            "Should return account.payment.method.line recordset",
        )

    def test_get_payment_methods_only_inbound(self):
        """_get_payment_methods only returns inbound payment method lines."""
        # Mark outbound lines as allowed too
        self.bank_journal.outbound_payment_method_line_ids.allowed_on_pms = True
        result = self.pms_property1._get_payment_methods()
        outbound_line_ids = set(self.bank_journal.outbound_payment_method_line_ids.ids)
        returned_ids = set(result.ids)
        self.assertFalse(
            returned_ids & outbound_line_ids,
            "Outbound payment method lines should not be returned",
        )

    # =========================================================================
    # do_payment tests
    # =========================================================================

    def test_do_payment_sets_payment_method_line(self):
        """do_payment creates account.payment with correct payment_method_line_id."""
        folio = self._create_folio_with_reservation()
        method_line = self.pms_property1._get_payment_methods()[0]
        payments_before = self.env["account.payment"].search(
            [("folio_ids", "in", folio.id)]
        )
        self.env["pms.folio"].do_payment(
            payment_method_line=method_line,
            user=self.env.user,
            amount=folio.pending_amount,
            folio=folio,
            partner=folio.partner_id,
        )
        payment = self.env["account.payment"].search(
            [("folio_ids", "in", folio.id), ("id", "not in", payments_before.ids)]
        )
        self.assertEqual(
            payment.payment_method_line_id,
            method_line,
            "Payment should have the payment_method_line_id used in do_payment",
        )
        self.assertEqual(
            payment.journal_id,
            method_line.journal_id,
            "Payment journal should be derived from the payment method line",
        )

    # =========================================================================
    # Wizard tests
    # =========================================================================

    def _create_wizard_form(self, folio):
        wizard_form = Form(
            self.env["wizard.payment.folio"].with_context(active_id=folio.id)
        )
        wizard_form.folio_id = folio
        wizard_form.amount = folio.pending_amount
        return wizard_form

    def test_wizard_available_journal_ids(self):
        """Wizard computes available_journal_ids from allowed method lines."""
        folio = self._create_folio_with_reservation()
        wizard_form = self._create_wizard_form(folio)
        wizard_form.journal_id = self.bank_journal
        wizard = wizard_form.save()
        self.assertIn(
            self.bank_journal,
            wizard.available_journal_ids,
            "Bank journal with allowed lines should be in available journals",
        )

    def test_wizard_method_lines_filtered_by_journal(self):
        """Wizard computes available_payment_method_line_ids filtered by journal."""
        folio = self._create_folio_with_reservation()
        wizard_form = self._create_wizard_form(folio)
        wizard_form.journal_id = self.bank_journal
        wizard = wizard_form.save()
        for line in wizard.available_payment_method_line_ids:
            self.assertEqual(
                line.journal_id,
                self.bank_journal,
                "All available method lines should belong to the selected journal",
            )

    def test_wizard_onchange_journal_selects_first_line(self):
        """Onchange journal auto-selects the first available payment method line."""
        folio = self._create_folio_with_reservation()
        wizard_form = self._create_wizard_form(folio)
        wizard_form.journal_id = self.bank_journal
        wizard = wizard_form.save()
        self.assertTrue(
            wizard.payment_method_line_id,
            "Onchange should auto-select a payment method line",
        )
        self.assertIn(
            wizard.payment_method_line_id,
            wizard.available_payment_method_line_ids,
            "Auto-selected line should be among available lines",
        )

    def test_wizard_onchange_journal_clears_line_if_no_methods(self):
        """Onchange clears payment_method_line_id when journal has no allowed lines."""
        folio = self._create_folio_with_reservation()
        # Create a journal with no allowed inbound lines
        empty_journal = self.env["account.journal"].create(
            {
                "name": "Empty Bank",
                "type": "bank",
                "code": "EBNK",
                "company_id": self.pms_property1.company_id.id,
            }
        )
        empty_journal.inbound_payment_method_line_ids.allowed_on_pms = False
        wizard_form = self._create_wizard_form(folio)
        # First set a valid journal so the form is happy
        wizard_form.journal_id = self.bank_journal
        # Now switch to the empty journal
        wizard_form.journal_id = empty_journal
        self.assertFalse(
            wizard_form.payment_method_line_id,
            "Payment method line should be cleared when journal has no allowed lines",
        )
