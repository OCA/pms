from odoo import _, api, fields, models
from odoo.exceptions import UserError


class InvoiceFilterDays(models.TransientModel):

    _name = "pms.invoice.filter.days"
    _description = "Filter Days"

    @api.model
    def default_reservation_lines(self):
        return (
            self.env["account.move.line"]
            .browse(self.env.context.get("active_ids"))
            .reservation_line_ids
        )

    @api.model
    def default_move_lines(self):
        return self.env["account.move.line"].browse(self.env.context.get("active_ids"))

    @api.model
    def default_from_date(self):
        return min(
            self.env["account.move.line"]
            .browse(self.env.context.get("active_ids"))
            .reservation_line_ids.mapped("date")
        )

    @api.model
    def default_to_date(self):
        return max(
            self.env["account.move.line"]
            .browse(self.env.context.get("active_ids"))
            .reservation_line_ids.mapped("date")
        )

    move_line_ids = fields.Many2many("account.move.line", default=default_move_lines)
    move_ids = fields.Many2many("account.move", compute="_compute_move_ids")
    reservation_line_ids = fields.Many2many(
        "pms.reservation.line", default=default_reservation_lines
    )
    from_date = fields.Date("Date From", default=default_from_date)
    to_date = fields.Date("Date to", default=default_to_date)
    date_ids = fields.One2many(
        comodel_name="pms.invoice.filter.days.items",
        inverse_name="filter_wizard_id",
        compute="_compute_date_ids",
        store=True,
        readonly=False,
    )

    def do_filter(self):
        self.ensure_one()
        invoice_lines = self.move_line_ids
        for line in invoice_lines:
            reservation_lines = line.reservation_line_ids.filtered(
                lambda d: d.date in self.date_ids.filtered("included").mapped("date")
            )
            if not reservation_lines:
                raise UserError(_("You can not remove all lines for invoice"))
            else:
                # Write on invoice for syncr business/account
                line.move_id.write(
                    {
                        "invoice_line_ids": [
                            (
                                1,
                                line.id,
                                {
                                    "reservation_line_ids": [
                                        (6, False, reservation_lines.ids)
                                    ],
                                    "quantity": len(reservation_lines),
                                },
                            )
                        ]
                    }
                )

    @api.depends("from_date", "to_date", "reservation_line_ids")
    def _compute_date_ids(self):
        self.ensure_one()
        date_list = [(5, 0, 0)]
        dates = self.reservation_line_ids.filtered(
            lambda d: d.date >= self.from_date and d.date <= self.to_date
        ).mapped("date")
        for date in dates:
            date_list.append(
                (
                    0,
                    False,
                    {
                        "date": date,
                    },
                )
            )
        self.date_ids = date_list

    @api.depends("move_line_ids")
    def _compute_move_ids(self):
        self.ensure_one()
        self.move_ids = [(6, 0, self.move_line_ids.mapped("move_id.id"))]


class InvoiceFilterDaysItems(models.TransientModel):

    _name = "pms.invoice.filter.days.items"
    _description = "Item Days"
    _rec_name = "date"

    date = fields.Date("Date")
    included = fields.Boolean("Included", default=True)
    filter_wizard_id = fields.Many2one(comodel_name="pms.invoice.filter.days")
