from odoo import models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def next_by_id(self, sequence_date=None):
        seq = self.env['ir.sequence'].browse(self.id)

        if seq.number_next == 1000:
            seq.number_next = 1
            # seq._set_number_next_actual()

        result = super(IrSequence, self).next_by_id()

        return result
