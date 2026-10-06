# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsPricelistOccupancy(models.Model):
    _name = "pms.pricelist.occupancy"
    _description = "Occupancy price modifiers of a pricelist for a room type"
    _check_pms_properties_auto = True

    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist these modifiers belong to",
        comodel_name="product.pricelist",
        required=True,
        index=True,
        ondelete="cascade",
        check_pms_properties=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room type these modifiers apply to",
        comodel_name="pms.room.type",
        required=True,
        index=True,
        ondelete="cascade",
        check_pms_properties=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties of the room type these modifiers apply to",
        comodel_name="pms.property",
        related="room_type_id.pms_property_ids",
    )
    increase_mode = fields.Selection(
        help="How to charge each guest above the default occupancy",
        selection=[("percent", "Percentage"), ("amount", "Fixed amount")],
        default="percent",
        required=True,
    )
    increase_value = fields.Float(
        string="Increase",
        help="Charged for each guest above the default occupancy of the room "
        "type. Zero to charge the same price no matter how many they are",
        digits=("Product Price"),
    )
    decrease_mode = fields.Selection(
        help="How to discount each guest below the default occupancy",
        selection=[("percent", "Percentage"), ("amount", "Fixed amount")],
        default="percent",
        required=True,
    )
    decrease_value = fields.Float(
        string="Decrease",
        help="Discounted for each guest below the default occupancy of the "
        "room type. Zero to charge the same price no matter how many they are",
        digits=("Product Price"),
    )
    summary = fields.Char(
        string="Per Guest",
        help="What each guest of difference changes in the price",
        compute="_compute_summary",
    )

    _sql_constraints = [
        (
            "pricelist_room_type_uniq",
            "unique(pricelist_id, room_type_id)",
            "A room type can only have one occupancy configuration per " "pricelist.",
        )
    ]

    @api.depends("increase_mode", "increase_value", "decrease_mode", "decrease_value")
    def _compute_summary(self):
        """A one-liner for the list, so the form holds the detail."""
        for record in self:
            parts = record._summary_parts()
            record.summary = " / ".join(parts) if parts else _("Same price")

    def _summary_parts(self):
        """The pieces of the summary, one per modifier that is set."""
        self.ensure_one()
        parts = []
        if self.increase_value:
            modifier = self._format_modifier(self.increase_mode, self.increase_value)
            parts.append(f"+{modifier}")
        if self.decrease_value:
            modifier = self._format_modifier(self.decrease_mode, self.decrease_value)
            parts.append(f"-{modifier}")
        return parts

    def _format_modifier(self, mode, value):
        self.ensure_one()
        if mode == "percent":
            return f"{value:g}%"
        return f"{value:g} {self.pricelist_id.currency_id.symbol or ''}"

    @api.constrains("increase_value", "decrease_value")
    def _check_values_not_negative(self):
        """The direction is given by the field, so the value is an amount.

        A negative increase would silently discount, and the other way round.
        """
        for record in self:
            if record.increase_value < 0 or record.decrease_value < 0:
                raise ValidationError(
                    _("Occupancy increase and decrease can't be negative.")
                )

    def _apply(self, price, difference):
        """Price for an occupancy differing by `difference` guests.

        The modifier is linear: it applies once per guest of difference, which
        is what channel managers derive from a default occupancy as well.
        """
        self.ensure_one()
        if difference > 0:
            mode, value, guests, sign = (
                self.increase_mode,
                self.increase_value,
                difference,
                1,
            )
        else:
            mode, value, guests, sign = (
                self.decrease_mode,
                self.decrease_value,
                -difference,
                -1,
            )
        if not value:
            return price
        if mode == "percent":
            return price * (1 + sign * value * guests / 100)
        return price + sign * value * guests
