import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base_vat.models.res_partner import _eu_country_vat

CODE_SPAIN = "ES"

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    ine_code = fields.Char(
        string="INE State Code",
        compute="_compute_ine_code",
        store=True,
    )

    @api.depends("nationality_id", "residence_state_id")
    def _compute_ine_code(self):
        for record in self:
            if not record.nationality_id:
                record.ine_code = False
            elif record.nationality_id.code != CODE_SPAIN:
                record.ine_code = record.nationality_id.code_alpha3
            else:
                if not record.residence_state_id:
                    record.ine_code = False
                record.ine_code = record.residence_state_id.ine_code

    def _check_enought_invoice_data(self):
        self.ensure_one()
        res = super(ResPartner, self)._check_enought_invoice_data()
        if not res:
            return res
        if not self.country_id or not self.city or not (self.street or self.street2):
            return False
        if not self.vat:
            if self.country_id.code == "ES":
                return False
            elif not self.aeat_identification:
                return False
        return True

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        # REVIEW: Force Contrain vat
        # https://github.com/odoo/odoo/issues/23242
        for partner in self:
            if vals.get("vat") or vals.get("country_id"):
                country = (
                    self.env["res.country"].browse(vals.get("country_id"))
                    or partner.country_id
                )
                if country.code == "ES":
                    self.check_vat()
                self._pms_check_unique_vat()
        return res

    @api.model
    def create(self, vals):
        records = super(ResPartner, self).create(vals)
        # REVIEW: Force Contrain vat
        # https://github.com/odoo/odoo/issues/23242
        if vals.get("vat") and vals.get("country_id"):
            country = self.env["res.country"].browse(vals.get("country_id"))
            if country.code == "ES":
                self.check_vat()
            records._pms_check_unique_vat()
        return records

    # This function is a candidate to be moved to the module
    # partner_vat_unique
    def _pms_check_unique_vat(self):
        for partner in self.filtered(lambda p: p.vat and p.country_id):
            repeat_partner = self._get_repeat_partner(partner)
            if bool(partner.vat) and not partner.parent_id and repeat_partner:
                raise UserError(
                    _("The VAT number %s already exists in other contacts: %s")
                    % (
                        repeat_partner.vat,
                        repeat_partner.name,
                    )
                )

    def _get_repeat_partner(self, partner):
        europe = self.env.ref("base.europe")
        if not europe:
            europe = self.env["res.country.group"].search(
                [("name", "=", "Europe")], limit=1
            )
        partner_country_code = partner.commercial_partner_id.country_id.code
        vat_country, vat_number = self._split_vat(partner.vat)
        if europe and partner.country_id.id in europe.country_ids.ids:
            vat_country = _eu_country_vat.get(vat_country, vat_country).upper()
        vat_with_code = (
            partner.vat
            if partner_country_code.upper() == vat_country.upper()
            else partner_country_code.upper() + partner.vat
        )
        vat_without_code = (
            partner.vat
            if partner_country_code.upper() != vat_country.upper()
            else vat_number
        )
        domain = [
            ("company_id", "in", [False, partner.company_id.id]),
            "|",
            ("vat", "=", vat_with_code),
            ("vat", "=", vat_without_code),
        ]
        domain += [("id", "!=", partner.id), "!", ("id", "child_of", partner.id)]
        return self.with_context(active_test=False).search(domain, limit=1)

    def _missing_document(self, vals, partners=False):
        res = super(ResPartner, self)._missing_document(vals, partners)
        if not res:
            return res
        if (
            vals.get("aeat_identification") is False
            or vals.get("aeat_identification") == ""
            or (
                "aeat_identification" not in vals
                and (
                    any([not partner.aeat_identification for partner in partners])
                    if partners
                    else True
                )
            )
        ):
            return True
        return False

    @api.constrains("country_id", "vat")
    def update_vat_code_country(self):
        if self.env.context.get("ignore_vat_update"):
            return
        for record in self:
            country_id = record.country_id.id
            vat = record.vat
            if vat and country_id:
                vat_with_code = record.fix_eu_vat_number(country_id, vat)
                if country_id and vat != vat_with_code:
                    record.with_context({"ignore_vat_update": True}).write(
                        {"vat": vat_with_code}
                    )
