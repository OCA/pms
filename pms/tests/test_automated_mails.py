from odoo.exceptions import UserError

from .common import TestPms


class TestPmsAutomatedMails(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env["mail.template"].search(
            [("name", "=", "Confirmed Reservation")]
        )

    def test_create_automated_action(self):
        """
        Checks that an automated_action is created correctly when an
        automated_mail is created.
        ---------------------
        An automated_mail is created and then it is verified that
        the automated_action was created.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "creation",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertTrue(
            auto_mail.automated_actions_id, "Automated action should be created "
        )

    def test_no_action_creation_before(self):
        """
        Check that an automated mail cannot be created with action='creation'
        and moment='before'.
        -----------------------
        An automated mail is created with action = 'creation' and moment = 'before'.
        Then it is verified that a UserError was thrown because an automated_mail with
        these parameters cannot be created.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "creation",
            "moment": "before",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT & ASSERT
        with self.assertRaises(
            UserError,
            msg="It should not be allowed to create the automated mail "
            "with action 'creation' and moment 'before' values",
        ):
            self.env["pms.automated.mails"].create(automated_mail_vals)

    def test_trigger_moment_in_act_creation(self):
        """
        Check that when creating an automated mail with parameters
        action = 'creation' and moment = 'in_act' the trigger of the
         automated_action created is 'on_create'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "creation",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_create",
            "The trigger of the automated action must be 'on_create'",
        )

    def test_trigger_moment_after_in_creation_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'creation' and moment = 'after' the trigger of the
        automated_action created is 'on_time'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "creation",
            "moment": "after",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            "time": 1,
            "time_type": "hour",
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_time",
            "The trigger of the automated action must be 'on_time'",
        )

    def test_trigger_moment_in_act_in_write_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'write' and moment = 'in_act' the trigger of the
        automated_action created is 'on_write'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "write",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_write",
            "The trigger of the automated action must be 'on_write'",
        )

    def test_trigger_moment_after_in_write_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'write' and moment = 'after' the trigger of the
        automated_action created is 'on_time'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "write",
            "moment": "after",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            "time": 1,
            "time_type": "hour",
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_time",
            "The trigger of the automated action must be 'on_time'",
        )

    def test_time_moment_before_in_checkin(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkin' and moment = 'before' the trg_date_range
        of the automated_action created is equal to
        (automated_mail.time * -1)'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkin",
            "moment": "before",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            "time": 60,
            "time_type": "minutes",
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trg_date_range,
            -60,
            "The trg_date_range of the automated action must be '-60'",
        )

    def test_time_moment_in_act_in_checkin(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkin' and moment = 'in_act' the trg_date_range
        of the automated_action created is equal to 0
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkin",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trg_date_range,
            0,
            "The trg_date_range of the automated action must be '0'",
        )

    def test_trigger_moment_before_in_checkin(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkin' and moment = 'before' the trigger of the
        automated_action created is 'on_time'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkin",
            "moment": "before",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            "time": 24,
            "time_type": "hour",
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_time",
            "The trigger of the automated action must be 'on_time'",
        )

    def test_trigger_moment_in_act_in_checkin(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkin' and moment = 'in_act' the trigger of the
        automated_action created is 'on_write'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkin",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_write",
            "The trigger of the automated action must be 'on_write'",
        )

    def test_time_moment_in_act_in_checkout(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkout' and moment = 'in_act' the trg_date_range
        of the automated_action created is equal to 0.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkout",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trg_date_range,
            0,
            "The trg_date_range of the automated action must be '0'",
        )

    def test_trigger_moment_before_in_checkout(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkout' and moment = 'before' the trigger of the
        automated_action created is 'on_time'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkout",
            "moment": "before",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            "time": 24,
            "time_type": "hour",
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_time",
            "The trigger of the automated action must be 'on_time'",
        )

    def test_trigger_moment_in_act_in_checkout(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkout' and moment = 'in_act' the trigger of the
        automated_action created is 'on_write'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkout",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_write",
            "The trigger of the automated action must be 'on_write'",
        )

    def test_trigger_moment_in_act_in_payment_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'payment' and moment = 'in_act' the trigger of the
        automated_action created is 'on_create'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "payment",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_create",
            "The trigger of the automated action must be 'on_create'",
        )

    def test_trigger_moment_before_in_payment_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'payment' and moment = 'before' the trigger of the
        automated_action created is 'on_time'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "payment",
            "moment": "before",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            "time": 24,
            "time_type": "hour",
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_time",
            "The trigger of the automated action must be 'on_time'",
        )

    def test_time_moment_before_in_payment_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'payment' and moment = 'before' the trg_date_range
        field of the automated_action is (automated_mail.time * -1).
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "payment",
            "moment": "before",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            "time": 24,
            "time_type": "hour",
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trg_date_range,
            -24,
            "The trg_date_range of the automated action must be '-24'",
        )

    def test_trigger_moment_in_act_in_invoice_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'invoice' and moment = 'in_act' the trigger field
        of the automated_action created is 'on_create'.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "invoice",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trigger,
            "on_create",
            "The trigger of the automated action must be 'on_create'",
        )

    def test_time_moment_in_act_in_invoice_action(self):
        """
        Check that when creating an automated mail with parameters
        action = 'invoice' and moment = 'in_act' the trg_date_range
        field of the automated_action is 0.
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "invoice",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.trg_date_range,
            0,
            "The trg_date_range of the automated action must be '0'",
        )

    def test_filter_pre_domain_moment_in_act_in_checkin(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkin' and moment = 'in_act' the filter_pre_domain
        field of the automated_action is [('state', '=', 'confirm')].
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkin",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.filter_pre_domain,
            "[('state', '=', 'confirm')]",
            "The filter_pre_domain of the automated action "
            "must be '[('state', '=', 'confirm')]'",
        )

    def test_filter_domain_moment_in_act_in_checkin(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkin' and moment = 'in_act' the filter_domain
        field of the automated_action is
        [('state', '=', 'onboard'),
         ('pms_property_id', '=', [value of property_id.id])]].
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkin",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)
        pms_property_id_str = str(auto_mail.pms_property_ids.ids)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.filter_domain,
            "[('state', '=', 'onboard'), ('pms_property_id', 'in', "
            + pms_property_id_str
            + ")]",
            "The filter_domain of the automated action must be "
            "'[('state', '=', 'onboard'), "
            "('pms_property_id', '=', [value of property_id.id])]'",
        )

    def test_filter_pre_domain_moment_in_act_in_checkout(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkout' and moment = 'in_act' the filter_pre_domain
        field of the automated_action is [('state', '=', 'onboard')].
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkout",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.filter_pre_domain,
            "[('state', '=', 'onboard')]",
            "The filter_pre_domain of the automated action must "
            "be '[('state', '=', 'onboard')]'",
        )

    def test_filter_domain_moment_in_act_in_checkout(self):
        """
        Check that when creating an automated mail with parameters
        action = 'checkout' and moment = 'in_act' the filter_domain
        field of the automated_action is
        [('state', '=', 'out'), ('pms_property_id', '=', [value of property_id.id])]].
        """
        # ARRANGE
        automated_mail_vals = {
            "name": "Auto Mail 1",
            "template_id": self.template.id,
            "action": "checkout",
            "moment": "in_act",
            "pms_property_ids": [(6, 0, [self.pms_property1.id])],
        }

        # ACT
        auto_mail = self.env["pms.automated.mails"].create(automated_mail_vals)
        pms_property_id_str = str(auto_mail.pms_property_ids.ids)

        # ASSERT
        self.assertEqual(
            auto_mail.automated_actions_id.filter_domain,
            "[('state', '=', 'done'), ('pms_property_id', 'in', "
            + pms_property_id_str
            + ")]",
            "The filter_pre_domain of the automated action must "
            "be '[('state', '=', 'out'), "
            "('pms_property_id', '=', [value of property_id.id])]",
        )
