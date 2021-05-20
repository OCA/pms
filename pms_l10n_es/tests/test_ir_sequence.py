from odoo.tests import common


class TestIrSequence(common.SavepointCase):
    def test_sequence_property(self):
        pms_property = self.env["pms.property"].search([])[0]
        value = pms_property.sequence_id.next_by_id()
        print("test", value)
