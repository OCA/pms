# Copyright 2021 Eric Antones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tests import common

from .common import setup_test_model  # , teardown_test_model
from .multi_pms_properties_tester import ChildTester, ParentTester

_logger = logging.getLogger(__name__)


@common.tagged("-at_install", "post_install")
class TestMultiPMSProperties(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestMultiPMSProperties, cls).setUpClass()
        model_classes = [ParentTester, ChildTester]
        setup_test_model(cls.env, model_classes)
        for mdl_cls in model_classes:
            tester_model = cls.env["ir.model"].search([("model", "=", mdl_cls._name)])
            # Access record
            cls.env["ir.model.access"].create(
                {
                    "name": "access.%s" % mdl_cls._name,
                    "model_id": tester_model.id,
                    "perm_read": 1,
                    "perm_write": 1,
                    "perm_create": 1,
                    "perm_unlink": 1,
                }
            )

    # @classmethod
    # def tearDownClass(cls):
    #     teardown_test_model(cls.env, [ParentTester])
    #     super(TestMultiPMSProperties, cls).tearDownClass()

    # def test_exist_attribute(self):
    #     parent = self.env["pms.parent.tester"].create({"name": "parent test"})
