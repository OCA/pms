# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Fields declaration
    reservation_ids = fields.Many2many(
        "pms.reservation",
        "reservation_move_rel",
        "move_line_id",
        "reservation_id",
        string="Reservations",
        readonly=True,
        copy=False,
    )
    service_ids = fields.Many2many(
        "pms.service",
        "service_line_move_rel",
        "move_line_id",
        "service_id",
        string="Services",
        readonly=True,
        copy=False,
    )
    reservation_line_ids = fields.Many2many(
        "pms.reservation.line",
        "reservation_line_move_rel",
        "move_line_id",
        "reservation_line_id",
        string="Reservation Lines",
        readonly=True,
        copy=False,
    )
    folio_line_ids = fields.Many2many(
        "folio.sale.line",
        "folio_sale_line_invoice_rel",
        "invoice_line_id",
        "sale_line_id",
        string="Folio Lines",
        copy=False,
    )
    folio_ids = fields.Many2many(
        "pms.folio",
        "payment_folio_rel",
        "move_id",
        "folio_id",
        string="Folios",
        ondelete="cascade",
        compute="_compute_folio_ids",
        readonly=False,
        store=True,
    )
    name = fields.Char(
        compute="_compute_name",
        readonly=False,
        store=True,
    )

    @api.depends("service_ids", "reservation_ids")
    def _compute_folio_ids(self):
        for record in self:
            if record.service_ids:
                record.folio_ids = record.mapped("service_ids.folio_id")
            elif record.reservation_ids:
                record.folio_ids = record.mapped("reservation_ids.folio_id")
            elif not record.folio_ids:
                record.folio_ids = False

    def invoice_filter_days(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "pms.pms_invoice_filter_days_action"
        )
        # Force the values of the move line in the context to avoid issues
        ctx = dict(self.env.context)
        ctx.pop("active_id", None)
        ctx["active_ids"] = self.ids
        ctx["active_model"] = "account.move.line"
        action["context"] = ctx
        return action

    def _copy_data_extend_business_fields(self, values):
        super(AccountMoveLine, self)._copy_data_extend_business_fields(values)
        values["folio_line_ids"] = [(6, None, self.folio_line_ids.ids)]
        values["reservation_line_ids"] = [(6, None, self.reservation_line_ids.ids)]
        values["service_ids"] = [(6, None, self.service_ids.ids)]
        values["reservation_ids"] = [(6, None, self.reservation_ids.ids)]

    @api.depends("reservation_line_ids")
    def _compute_name(self):
        if hasattr(super(), "_compute_name"):
            super()._compute_field()
        for record in self:
            if record.reservation_line_ids:
                record.name = record._get_compute_name()

    def _get_compute_name(self):
        self.ensure_one()
        if self.reservation_line_ids:
            month = False
            name = False
            lines = self.reservation_line_ids.sorted("date")
            for date in lines.mapped("date"):
                if date.month != month:
                    name = name + "\n" if name else ""
                    name += date.strftime("%B-%Y") + ": "
                    name += date.strftime("%d")
                    month = date.month
                else:
                    name += ", " + date.strftime("%d")
            return name
        else:
            return False
