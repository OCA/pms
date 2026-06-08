# Copyright (c) 2021 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    reservation_ok = fields.Boolean(
        related="product_id.reservation_ok", readonly=True, string="Is Reservation?"
    )
    pms_reservation_id = fields.Many2one("pms.reservation", string="Reservation")

    def _compute_price_unit(self):
        pms_lines = self.filtered("pms_reservation_id")
        return super(SaleOrderLine, self - pms_lines)._compute_price_unit()

    @api.onchange("pms_reservation_id")
    def _onchange_pms_reservation_id(self):
        if self.pms_reservation_id and self.product_id:
            self.name = self._get_sale_order_line_multiline_description_sale()

    def _get_sale_order_line_multiline_description_sale(self):
        reservation = self.pms_reservation_id
        if reservation and self.product_id:
            desc = super()._get_sale_order_line_multiline_description_sale()
            parts = []
            if reservation.property_id:
                parts.append(reservation.property_id.display_name)
            if reservation.start and reservation.stop:
                parts.append(
                    "{} – {}".format(
                        reservation.start.strftime("%b %d, %Y"),
                        reservation.stop.strftime("%b %d, %Y"),
                    )
                )
            if reservation.no_of_guests:
                n = reservation.no_of_guests
                parts.append("{} Guest{}".format(n, "s" if n != 1 else ""))
            if parts:
                desc += "\n" + "\n".join(parts)
            return desc
        return super()._get_sale_order_line_multiline_description_sale()

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if rec.pms_reservation_id and not rec.pms_reservation_id.sale_order_line_id:
                rec.pms_reservation_id.sudo().write(
                    {
                        "sale_order_id": rec.order_id.id,
                        "sale_order_line_id": rec.id,
                    }
                )
            prop = rec.pms_reservation_id.property_id
            if prop and prop.analytic_id:
                rec.analytic_distribution = {str(prop.analytic_id.id): 100}
        return recs

    def write(self, values):
        rec = super().write(values)
        if values.get("pms_reservation_id"):
            for line in self:
                reservation = line.pms_reservation_id
                if reservation and not reservation.sale_order_line_id:
                    reservation.sudo().write(
                        {
                            "sale_order_id": line.order_id.id,
                            "sale_order_line_id": line.id,
                        }
                    )
                prop = reservation.property_id if reservation else False
                if prop and prop.analytic_id:
                    line.analytic_distribution = {str(prop.analytic_id.id): 100}
        return rec

    def unlink(self):
        for line in self:
            if line.product_id.reservation_ok and line.pms_reservation_id:
                line.pms_reservation_id.action_cancel()
        return super().unlink()

    def _prepare_invoice_line(self, **optional_values):
        result = super()._prepare_invoice_line(**optional_values)
        self.ensure_one()
        if self.pms_reservation_id and self.pms_reservation_id.property_id:
            result.update(
                {
                    "pms_reservation_id": self.pms_reservation_id.id,
                    "property_ids": [(6, 0, self.pms_reservation_id.property_id.ids)],
                }
            )
        return result
