# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsServiceLine(models.Model):
    _name = "pms.service.line"
    _description = "Service by day"
    _order = "date"
    _rec_name = "service_id"
    _check_pms_properties_auto = True

    service_id = fields.Many2one(
        string="Service Room",
        help="Service identifier",
        required=True,
        copy=False,
        comodel_name="pms.service",
        ondelete="cascade",
    )
    is_board_service = fields.Boolean(
        string="Is Board Service",
        help="Indicates if the service line is part of a board service",
        store=True,
        related="service_id.is_board_service",
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with this service line",
        store=True,
        related="service_id.product_id",
        check_pms_properties=True,
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        help="Taxes applied in the service line",
        readonly="True",
        comodel_name="account.tax",
        related="service_id.tax_ids",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the service belongs",
        readonly=True,
        store=True,
        comodel_name="pms.property",
        related="service_id.pms_property_id",
        check_pms_properties=True,
    )
    date = fields.Date(
        string="Date",
        help="Sate on which the product is to be consumed",
    )
    day_qty = fields.Integer(
        string="Units",
        help="Amount to be consumed per day",
    )
    price_unit = fields.Float(
        string="Unit Price",
        help="Price per unit of service",
        digits=("Product Price"),
    )
    price_day_subtotal = fields.Monetary(
        string="Subtotal",
        help="Subtotal price without taxes",
        readonly=True,
        store=True,
        compute="_compute_day_amount_service",
    )
    price_day_total = fields.Monetary(
        string="Total",
        help="Total price without taxes",
        readonly=True,
        store=True,
        compute="_compute_day_amount_service",
    )
    price_day_tax = fields.Float(
        string="Taxes Amount",
        help="",
        readonly=True,
        store=True,
        compute="_compute_day_amount_service",
    )
    currency_id = fields.Many2one(
        string="Currency",
        help="The currency used in relation to the service where it's included",
        readonly=True,
        store=True,
        related="service_id.currency_id",
    )
    reservation_id = fields.Many2one(
        string="Reservation",
        help="Room to which the services will be applied",
        readonly=True,
        store=True,
        related="service_id.reservation_id",
        check_pms_properties=True,
    )
    discount = fields.Float(
        string="Discount (%)",
        help="Discount in the price of the service.",
        readonly=False,
        store=True,
        default=0.0,
        digits=("Discount"),
        compute="_compute_discount",
    )
    cancel_discount = fields.Float(
        string="Cancelation Discount",
        help="",
        compute="_compute_cancel_discount",
        readonly=True,
        store=True,
    )
    auto_qty = fields.Boolean(
        string="Qty automated setted",
        help="Show if the day qty was calculated automatically",
        compute="_compute_auto_qty",
        readonly=False,
        store=True,
    )

    @api.depends("day_qty", "discount", "price_unit", "tax_ids")
    def _compute_day_amount_service(self):
        for line in self:
            amount_service = line.price_unit
            if amount_service > 0:
                currency = line.service_id.currency_id
                product = line.product_id
                price = amount_service * (1 - (line.discount or 0.0) * 0.01)
                # REVIEW: line.day_qty is not the total qty (the total is on service_id)
                taxes = line.tax_ids.compute_all(
                    price, currency, line.day_qty, product=product
                )
                line.update(
                    {
                        "price_day_tax": sum(
                            t.get("amount", 0.0) for t in taxes.get("taxes", [])
                        ),
                        "price_day_total": taxes["total_included"],
                        "price_day_subtotal": taxes["total_excluded"],
                    }
                )
            else:
                line.update(
                    {
                        "price_day_tax": 0,
                        "price_day_total": 0,
                        "price_day_subtotal": 0,
                    }
                )

    @api.depends("service_id.reservation_id", "service_id.reservation_id.discount")
    def _compute_discount(self):
        """
        On board service the line discount is always
        equal to reservation line discount
        """
        for record in self:
            if record.is_board_service:
                record.discount = (
                    record.service_id.reservation_id.reservation_line_ids.filtered(
                        lambda l: l.date == record.date
                    ).discount
                )
            elif not record.discount:
                record.discount = 0

    # TODO: Refact method and allowed cancelled single days
    @api.depends("service_id.reservation_id.cancelled_reason")
    def _compute_cancel_discount(self):
        for line in self:
            line.cancel_discount = 0
            # TODO: Review cancel logic
            # reservation = line.reservation_id.reservation_id
            # pricelist = reservation.pricelist_id
            # if reservation.state == "cancelled":
            #     if (
            #         reservation.cancelled_reason
            #         and pricelist
            #         and pricelist.cancelation_rule_id
            #     ):
            #         date_start_dt = fields.Date.from_string(
            #             reservation.checkin
            #         )
            #         date_end_dt = fields.Date.from_string(
            #             reservation.checkout
            #         )
            #         days = abs((date_end_dt - date_start_dt).days)
            #         rule = pricelist.cancelation_rule_id
            #         if reservation.cancelled_reason == "late":
            #             discount = 100 - rule.penalty_late
            #             if rule.apply_on_late == "first":
            #                 days = 1
            #             elif rule.apply_on_late == "days":
            #                 days = rule.days_late
            #         elif reservation.cancelled_reason == "noshow":
            #             discount = 100 - rule.penalty_noshow
            #             if rule.apply_on_noshow == "first":
            #                 days = 1
            #             elif rule.apply_on_noshow == "days":
            #                 days = rule.days_late - 1
            #         elif reservation.cancelled_reason == "intime":
            #             discount = 100

            #         checkin = reservation.checkin
            #         dates = []
            #         for i in range(0, days):
            #             dates.append(
            #                 (
            #                     fields.Date.from_string(checkin) + timedelta(days=i)
            #                 ).strftime(DEFAULT_SERVER_DATE_FORMAT)
            #             )
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date in dates
            #         ).update({"cancel_discount": discount})
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date not in dates
            #         ).update({"cancel_discount": 100})
            #     else:
            #         reservation.reservation_line_ids.update({"cancel_discount": 0})
            # else:
            #     reservation.reservation_line_ids.update({"cancel_discount": 0})

    @api.depends("day_qty")
    def _compute_auto_qty(self):
        """
        Set auto_qty = False if the service is no linked to room or
        if the day_qty was set manually
        (See autogeneration of service lines in
        _compute_service_line_ids -pms.service-)
        """
        self.auto_qty = False

    # Constraints and onchanges
    @api.constrains("day_qty")
    def no_free_resources(self):
        for record in self:
            limit = record.product_id.daily_limit
            if limit > 0:
                out_qty = sum(
                    self.env["pms.service.line"]
                    .search(
                        [
                            ("product_id", "=", record.product_id.id),
                            ("date", "=", record.date),
                            ("service_id", "!=", record.service_id.id),
                        ]
                    )
                    .mapped("day_qty")
                )
                if limit < out_qty + record.day_qty:
                    raise ValidationError(
                        _("%s limit exceeded for %s")
                        % (record.service_id.product_id.name, record.date)
                    )

    # Business methods
    def _cancel_discount(self):
        for record in self:
            if record.reservation_id:
                day = record.reservation_id.reservation_line_ids.filtered(
                    lambda d: d.date == record.date
                )
                record.cancel_discount = day.cancel_discount
