# Copyright 2004-2010 Tiny SPRL http://tiny.be
# Copyright 2010-2012 ChriCar Beteiligungs- und Beratungs- GmbH
#             http://www.camptocamp.at
# Copyright 2015 Antiun Ingenieria, SL (Madrid, Spain)
#        http://www.antiun.com
#        Antonio Espinosa <antonioea@antiun.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
            if not record.valid_from and record.partner_id.pms_checkin_partner_ids:
                document_expedition_date = list(
                    set(
                        record.partner_id.pms_checkin_partner_ids.mapped(
                            "document_expedition_date"
                        )
                    )
                )
                if len(document_expedition_date) == 1:
                    record.valid_from = document_expedition_date[0]
                else:
                    record.valid_from = False
            elif not record.valid_from:
                record.valid_from = False

    @api.constrains("partner_id", "category_id")
    def _check_category_id_unique(self):
        for record in self:
            id_number = self.env["res.partner.id_number"].search(
                [
                    ("partner_id", "=", record.partner_id.id),
                    ("category_id", "=", record.category_id.id),
                ]
            )
            if len(id_number) > 1:
                raise ValidationError(_("Partner already has this document type"))
