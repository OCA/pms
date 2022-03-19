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
    vat_syncronized = fields.Boolean(
        help="Technical field to know if vat partner is syncronized with this document",
        compute="_compute_vat_syncronized",
        store=True,
    )

    @api.depends(
        "partner_id", "partner_id.pms_checkin_partner_ids.document_expedition_date"
    )
    def _compute_valid_from(self):
        if hasattr(super(), "_compute_valid_from"):
            super()._compute_valid_from()
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

    @api.depends("partner_id", "partner_id.vat", "name")
    def _compute_vat_syncronized(self):
        self.vat_syncronized = False
        for record in self:
            if record.partner_id and record.partner_id.vat and record.name:
                if record.name.upper() == record.partner_id.vat.upper():
                    record.vat_syncronized = True
            elif not record.partner_id.vat and record.name:
                record.vat_syncronized = True
            else:
                record.vat_syncronized = False
