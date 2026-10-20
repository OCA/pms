# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date

import babel

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="product_template_pms_property_rel",
        column1="product_tmpl_id",
        column2="pms_property_id",
        check_pms_properties=True,
        ondelete="restrict",
    )
    per_day = fields.Boolean(
        string="Unit increment per day",
        help="Indicates that the product is sold by days",
    )
    per_person = fields.Boolean(
        string="Unit increment per person",
        help="Indicates that the product is sold per person",
    )
    consumed_on = fields.Selection(
        string="Consumed",
        help="Indicates when the product is consumed",
        selection=[
            ("before", "All before night"),
            ("after", "All after night"),
            ("checkin", "Only first day"),
            ("checkout", "Only last day"),
        ],
        default="before",
    )
    daily_limit = fields.Integer(
        help="Indicates how much products can consumed in one day",
        compute="_compute_daily_limit",
        inverse="_inverse_daily_limit",
    )
    is_extra_bed = fields.Boolean(
        help="Indicates if that product is a extra bed, add +1 capacity in the room",
        default=False,
    )
    is_crib = fields.Boolean(
        string="Is a baby crib",
        help="Indicates if that product is a crib",
        default=False,
    )
    is_pms_available = fields.Boolean(
        string="Is available in PMS",
        help="Indicates if that product is available in PMS",
        default=True,
    )
    is_board_service = fields.Boolean(
        string="Is a board service",
        help="Indicates that the product is a board service (breakfast, half "
        "board...) that pricelists sell and reservations include. With the "
        "Guest attribute, adults and children consume their own variant",
        default=False,
    )
    board_show_detail_report = fields.Boolean(
        string="Show board service detail on report",
        help="If unchecked, the folio report adds the board service to the "
        "price of the room instead of showing it on its own lines",
    )
    is_tourist_tax = fields.Boolean(
        string="Is tourist tax",
        help="Indicates if that product is a tourist tax",
        default=False,
    )
    tourist_tax_date_start = fields.Selection(
        selection=lambda self: self._get_mmdd_selection(),
        string="Start Date (Annual)",
        required=False,
    )
    tourist_tax_date_end = fields.Selection(
        selection=lambda self: self._get_mmdd_selection(),
        string="End Date (Annual)",
        required=False,
    )
    tourist_tax_apply_from_night = fields.Integer(
        string="Apply From Night",
        default=1,
        help="Night number the rule starts applying (e.g., 1 = first night)",
    )
    tourist_tax_apply_to_night = fields.Integer(
        string="Apply Until Night",
        help="Night number the rule stops applying (optional)",
    )
    tourist_tax_min_age = fields.Integer(
        string="Minimum Age", help="Applies only to guests with this age or older"
    )
    tourist_tax_max_age = fields.Integer(
        string="Maximum Age", help="Applies only to guests up to this age"
    )
    property_daily_limits = fields.One2many(
        string="Daily Limits per Property",
        comodel_name="ir.pms.property",
        inverse_name="record",
        domain=lambda self: [
            ("model_id.model", "=", "product.template"),
            ("field_id.name", "=", "daily_limit"),
        ],
    )

    @api.depends_context("allowed_pms_property_ids")
    def _compute_daily_limit(self):
        for record in self:
            pms_property_id = self.env.context.get("property")
            record.daily_limit = self.env["ir.pms.property"].get_field_value(
                pms_property_id,
                self._name,
                "daily_limit",
                record.id,
                type(record.daily_limit),
            )

    def _inverse_daily_limit(self):
        for record in self:
            pms_property_id = self.env.context.get("property")
            self.env["ir.pms.property"].set_field_value(
                pms_property_id,
                self._name,
                "daily_limit",
                record.id,
                record.daily_limit,
            )

    def write(self, vals):
        if vals.get("is_tourist_tax") is True:
            vals["is_pms_available"] = True
            vals["per_day"] = True
            vals["consumed_on"] = "before"
        return super().write(vals)

    @api.constrains("is_board_service", "attribute_line_ids")
    def _check_board_service_attributes(self):
        board_services = self.filtered("is_board_service")
        if not board_services:
            return
        guest_attribute = self.env.ref("pms.product_attribute_board_guest")
        room_only = self._room_only_board_service()
        for record in board_services:
            attributes = record.attribute_line_ids.attribute_id
            if record == room_only and attributes:
                raise ValidationError(_("Room Only can't have variants"))
            if attributes - guest_attribute:
                raise ValidationError(
                    _(
                        "A board service can only have the attribute %s, "
                        "otherwise a reservation can't tell which variant "
                        "a guest consumes"
                    )
                    % guest_attribute.name
                )

    @api.constrains("is_board_service")
    def _check_room_only_is_board_service(self):
        if self._room_only_board_service() in self.filtered(
            lambda record: not record.is_board_service
        ):
            raise ValidationError(_("Room Only must be a board service"))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_room_only(self):
        if self._room_only_board_service() in self:
            raise UserError(_("Room Only can't be deleted"))

    @api.model
    def _room_only_board_service(self):
        return (
            self.env.ref(
                "pms.product_template_board_room_only", raise_if_not_found=False
            )
            or self.browse()
        )

    def _get_board_service_products(self, adults, children):
        """The products a stay with this board service consumes, each one with
        the guests it is counted by: the variants of the guests that are
        present. Room Only consumes nothing.

        :return: list of (product.product, guest type)
        """
        self.ensure_one()
        if self == self._room_only_board_service():
            return []
        guests = {"adults": adults, "children": children, "all": adults + children}
        return [
            (product, product.board_guest_type)
            for product in self.product_variant_ids
            if guests[product.board_guest_type]
        ]

    def _get_board_service_price(self, pricelist, pms_property, date, adults, children):
        """Price of one night of this board service for the guests of a room"""
        self.ensure_one()
        guests = {"adults": adults, "children": children, "all": adults + children}
        price = 0.0
        for product, guest_type in self._get_board_service_products(adults, children):
            unit_price = pricelist._get_product_price(
                product=product,
                quantity=1,
                consumption_date=date,
                pms_property_id=pms_property.id,
            )
            price += unit_price * (guests[guest_type] if product.per_person else 1)
        return price

    def _get_mmdd_selection(self):
        lang = self.env.lang or "en_US"
        days_by_month = {
            1: 31,
            2: 29,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30,
            12: 31,
        }

        options = []
        for month in range(1, 13):
            for day in range(1, days_by_month[month] + 1):
                mmdd = f"{month:02d}-{day:02d}"
                dt = date(2024, month, day)  # Dummy year
                label = babel.dates.format_date(dt, format="d MMMM", locale=lang)
                options.append((mmdd, label.capitalize()))
                # Capitalize first letter for consistency
        return options
