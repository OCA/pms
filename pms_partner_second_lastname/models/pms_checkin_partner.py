from odoo import api, fields, models


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    lastname2 = fields.Char(
        string="Second Last Name",
        help="host second lastname",
        readonly=False,
        store=True,
        compute="_compute_lastname2",
        inverse=lambda r: r._inverse_partner_fields("lastname2", "lastname2"),
    )

    @api.depends("partner_id")
    def _compute_lastname2(self):
        for record in self:
            if not record.lastname2 and record.partner_id.lastname2:
                record.lastname2 = record.partner_id.lastname2
            elif not record.lastname2:
                record.lastname2 = False

    @api.model
    def _checkin_manual_fields(self, country=False):
        manual_fields = super()._checkin_manual_fields(country=country)
        manual_fields.append("lastname2")
        return manual_fields

    @api.model
    def _checkin_partner_fields(self):
        checkin_fields = super()._checkin_partner_fields()
        checkin_fields.append("lastname2")
        return checkin_fields

    @api.model
    def _get_partner_incongruences_field_names(self):
        res = super()._get_partner_incongruences_field_names()
        res.append("lastname2")
        return res

    def _completed_partner_creation_fields(self):
        res = super()._completed_partner_creation_fields()
        if self.lastname2:
            return True
        return res

    def _get_partner_create_vals(self):
        res = super()._get_partner_create_vals()
        res["lastname2"] = self.lastname2
        return res
