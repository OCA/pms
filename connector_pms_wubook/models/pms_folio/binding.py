# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ChannelWubookPmsFolioBinding(models.Model):
    _name = "channel.wubook.pms.folio"
    _inherit = "channel.wubook.binding"
    _inherits = {"pms.folio": "odoo_id"}

    # binding fields
    odoo_id = fields.Many2one(
        comodel_name="pms.folio",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    wubook_status = fields.Selection(
        selection=[
            ("1", "Confirmed"),
            ("2", "Waiting for approval (only wubook reservations)"),
            ("3", "Refused (only wubook reservations)"),
            ("4", "Accepted (only wubook reservations)"),
            ("5", "Cancelled"),
            ("6", "(Probably not used anymore): cancelled with penalty]"),
            ("7", "Modified (New state, it does not exist on Wubook)"),
        ],
        string="Wubook Status",
    )

    payment_gateway_fee = fields.Float(
        string="Paid at source",
        default=0,
    )

    @api.model
    def import_data(self, backend_id, date_from, date_to, mark):
        """ Prepare the batch import of Folios from Channel """
        domain = []
        if date_from and date_to:
            domain += [
                ("date_arrival", ">=", date_from),
                ("date_arrival", "<=", date_to),
            ]

        return self.import_batch(backend_record=backend_id, domain=domain)
