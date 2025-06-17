from odoo import api, fields, models


class ResPartnerIdNumber(models.Model):
    _inherit = "res.partner.id_number"
    _description = "Partner ID Number"

    support_number = fields.Char(
        string="Support number",
        help="DNI support number",
        store=True,
        readonly=False,
        compute="_compute_support_number",
    )

    @api.depends("partner_id", "partner_id.pms_checkin_partner_ids.support_number")
    def _compute_support_number(self):
        res = None
        if hasattr(super(), "_compute_support_number"):
            res = super()._compute_support_number()
        for record in self:
            if record.partner_id.pms_checkin_partner_ids:
                last_update_support_number = (
                    record.partner_id.pms_checkin_partner_ids.filtered(
                        lambda x, r=record: x.document_id == r
                        and x.write_date
                        == max(
                            r.partner_id.pms_checkin_partner_ids.mapped("write_date")
                        )
                    )
                )
                if (
                    last_update_support_number
                    and last_update_support_number[0].support_number
                ):
                    record.support_number = last_update_support_number[0].support_number
        return res
