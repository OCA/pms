from odoo import api, fields, models


class ResPartnerIdNumber(models.Model):
    _inherit = "res.partner.id_number"
    _description = "Partner ID Number"

    support_number = fields.Char(
        string="Support number",
        help="DNI support number",
        compute="_compute_support_number",
    )

    @api.depends("partner_id", "partner_id.pms_checkin_partner_ids.support_number")
    def _compute_support_number(self):
        if hasattr(super(), "_compute_support_number"):
            super()._compute_support_number()
        for record in self:
            if not record.support_number and record.partner_id.pms_checkin_partner_ids:
                support_number = list(
                    set(
                        record.partner_id.pms_checkin_partner_ids.mapped(
                            "support_number"
                        )
                    )
                )
                if len(support_number) == 1:
                    record.support_number = support_number[0]
                else:
                    record.support_number = False
            elif not record.support_number:
                record.support_number = False
