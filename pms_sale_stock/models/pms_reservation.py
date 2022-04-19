# Copyright (C) 2022 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class PMSReservation(models.Model):
    _inherit = "pms.reservation"

    stock_check_ids = fields.One2many(
        "stock.location.content.check", "pms_reservation_id", string="Checkouts"
    )
    stock_check_count = fields.Integer(
        compute="_compute_calc_stock_check_count", string="Count"
    )

    def _compute_calc_stock_check_count(self):
        for rec in self:
            check_ids = (
                self.env["stock.location.content.check"]
                .search([("pms_reservation_id", "=", rec.id)])
                .ids
            )
            rec.stock_check_count = len(check_ids)

    def action_confirm(self):
        check_obj = self.env["stock.location.content.check"]
        for rec in self:
            if not rec.property_id.stock_location_id:
                raise UserError(
                    _("Please set the inventory location for the property.")
                )
            check_id = check_obj.create(
                {
                    "date": rec.stop,
                    "location_id": rec.property_id.stock_location_id.id,
                    "pms_reservation_id": rec.id,
                }
            )
            check_id._onchange_location_id()
        return super().action_confirm()

    def action_view_pms_checkouts(self):
        return self.env.ref(
            "pms_sale_stock.action_stock_content_location_check_pms"
        ).read()[0]
