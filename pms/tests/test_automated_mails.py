from odoo.exceptions import UserError
from .common import TestPms


class TestPmsAutomatedMails(TestPms):
    def setUp(self):
        super().setUp()
        self.template = self.env["mail.template"].search([("name", "=", "Confirmed Reservation")])

    def test_create_automated_action(self):
        # ARRANGE
        automated_mail_vals = {
            "name": 'Auto Mail 1',
            "template_id": self.template.id,
            "action": "creation",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertTrue(
            auto_mail.automated_actions_id,
            "Automated action should be created "
        )

    def test_no_action_creation_before(self):
        # ARRANGE
        automated_mail_vals = {
            "name": 'Auto Mail 1',
            "template_id": self.template.id,
            "action": "creation",
            "moment": "before",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT & ASSERT
        with self.assertRaises(
            UserError,
            msg="It should not be allowed to create the automated mail "
                "with action 'creation' and moment 'before' values"
        ):
            self.env["pms.automated.mails"].create(automated_mail_vals)


