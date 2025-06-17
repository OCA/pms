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

    name = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_name",
    )

    category_id = fields.Many2one(
        readonly=False,
        store=True,
        compute="_compute_category_id",
    )

    valid_from = fields.Date(
        readonly=False,
        store=True,
        compute="_compute_valid_from",
    )

    country_id = fields.Many2one(
        string="Country",
        comodel_name="res.country",
        help="Country of the document",
        compute="_compute_country_id",
        store=True,
        readonly=False,
    )

    # pylint: disable=W8110
    @api.depends("partner_id", "partner_id.pms_checkin_partner_ids.document_number")
    def _compute_name(self):
        if hasattr(super(), "_compute_name"):
            super()._compute_name()
        for record in self:
            if record.partner_id.pms_checkin_partner_ids:
                last_update_name = record.partner_id.pms_checkin_partner_ids.filtered(
                    lambda x, r=record: x.document_id == r
                    and x.write_date
                    == max(r.partner_id.pms_checkin_partner_ids.mapped("write_date"))
                )
                if last_update_name and last_update_name[0].document_number:
                    record.name = last_update_name[0].document_number

    # pylint: disable=W8110
    @api.depends(
        "partner_id", "partner_id.pms_checkin_partner_ids.document_expedition_date"
    )
    def _compute_valid_from(self):
        if hasattr(super(), "_compute_valid_from"):
            super()._compute_valid_from()
        for record in self:
            if record.partner_id.pms_checkin_partner_ids:
                last_update_valid_from = (
                    record.partner_id.pms_checkin_partner_ids.filtered(
                        lambda x, r=record: x.document_id == r
                        and x.write_date
                        == max(
                            r.partner_id.pms_checkin_partner_ids.mapped("write_date")
                        )
                    )
                )
                if (
                    last_update_valid_from
                    and last_update_valid_from[0].document_expedition_date
                ):
                    record.valid_from = last_update_valid_from[
                        0
                    ].document_expedition_date

    # pylint: disable=W8110
    @api.depends("partner_id", "partner_id.pms_checkin_partner_ids.document_type")
    def _compute_category_id(self):
        if hasattr(super(), "_compute_category_id"):
            super()._compute_category_id()
        for record in self:
            if record.partner_id.pms_checkin_partner_ids:
                last_update_category_id = (
                    record.partner_id.pms_checkin_partner_ids.filtered(
                        lambda x, r=record: x.document_id == r
                        and x.write_date
                        == max(
                            r.partner_id.pms_checkin_partner_ids.mapped("write_date")
                        )
                    )
                )
                if last_update_category_id and last_update_category_id[0].document_type:
                    record.category_id = last_update_category_id[0].document_type

    @api.depends("partner_id", "partner_id.pms_checkin_partner_ids.document_country_id")
    def _compute_country_id(self):
        for record in self:
            if record.partner_id.pms_checkin_partner_ids:
                last_update_document = (
                    record.partner_id.pms_checkin_partner_ids.filtered(
                        lambda x, r=record: x.document_id == r
                        and x.write_date
                        == max(
                            r.partner_id.pms_checkin_partner_ids.mapped("write_date")
                        )
                    )
                )
                if last_update_document and last_update_document[0].document_country_id:
                    record.country_id = last_update_document[0].document_country_id

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

    @api.constrains("country_id", "category_id")
    def _check_document_country_id_category_id_consistence(self):
        for record in self:
            if record.category_id and record.country_id:
                if (
                    record.category_id.country_ids
                    and record.country_id not in record.category_id.country_ids
                ):
                    raise ValidationError(
                        _("Country is not allowed for this document type")
                    )
