# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class PaymentReturn(models.Model):
    _inherit = "payment.return"

    # Fields declaration
    folio_id = fields.Many2one(
        string="Folio", help="Folio in payment return", comodel_name="pms.folio"
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property with access to the element",
        store=True,
        readonly=True,
        comodel_name="pms.property",
        related="folio_id.pms_property_id",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company for Payment Return",
        check_pms_properties=True,
    )

    def action_confirm(self):
        pay = super(PaymentReturn, self).action_confirm()
        if pay:
            folio_ids = []
            folios = self.env["pms.folio"].browse(folio_ids)
            for line in self.line_ids:
                payments = self.env["account.payment"].search(
                    [("move_line_ids", "in", line.move_line_ids.ids)]
                )
                folios_line = self.env["pms.folio"].browse(
                    payments.mapped("folio_id.id")
                )
                # for folio in folios_line:
                #     if self.id not in folio.return_ids.ids:
                #         folio.update({"return_ids": [(4, self.id)]})
                #     msg = _("Return of %s registered") % (line.amount)
                #     folio.message_post(subject=_("Payment Return"), body=msg)
                folios += folios_line
            folios.compute_amount()
