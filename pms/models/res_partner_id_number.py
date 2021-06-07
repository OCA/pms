# Copyright 2004-2010 Tiny SPRL http://tiny.be
# Copyright 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# Copyright 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class ResPartnerIdNumber(models.Model):
    _inherit = "res.partner.id_number"

    valid_from = fields.Date(
        readonly=False,
        store=True,
        compute="_compute_valid_from",
    )

    @api.depends(
        "partner_id", "partner_id.pms_checkin_partner_ids.document_expedition_date"
    )
    def _compute_valid_from(self):
        if hasattr(super(), "_compute_valid_from"):
            super()._compute_field()
        for record in self:
            expedition_date = record.partner_id.pms_checkin_partner_ids.mapped(
                "document_expedition_date"
            )
            if expedition_date:
                if not record.valid_from and expedition_date[0]:
                    record.valid_from = expedition_date[0]
