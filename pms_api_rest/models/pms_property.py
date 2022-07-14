from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    color_option_config = fields.Selection(
        string="Color Option Configuration",
        help="Configuration of the color code for the planning.",
        selection=[("simple", "Simple"), ("advanced", "Advanced")],
        default="simple",
    )

    simple_out_color = fields.Char(
        string="Reservations Outside",
        help="Color for done reservations in the planning.",
        default="rgba(94,208,236)",
    )

    simple_in_color = fields.Char(
        string="Reservations Inside",
        help="Color for onboard and departure_delayed reservations in the planning.",
        default="rgba(0,146,183)",
    )

    simple_future_color = fields.Char(
        string="Future Reservations",
        help="Color for confirm, arrival_delayed and draft reservations in the planning.",
        default="rgba(1,182,227)",
    )

    pre_reservation_color = fields.Char(
        string="Pre-Reservation",
        help="Color for draft reservations in the planning.",
        default="rgba(162,70,128)",
    )

    confirmed_reservation_color = fields.Char(
        string="Confirmed Reservation",
        default="rgba(1,182,227)",
        help="Color for confirm reservations in the planning.",
    )

    paid_reservation_color = fields.Char(
        string="Paid Reservation",
        help="Color for done paid reservations in the planning.",
        default="rgba(126,126,126)",
    )

    on_board_reservation_color = fields.Char(
        string="Checkin",
        help="Color for onboard not paid reservations in the planning.",
        default="rgba(255,64,64)",
    )

    paid_checkin_reservation_color = fields.Char(
        string="Paid Checkin",
        help="Color for onboard paid reservations in the planning.",
        default="rgba(130,191,7)",
    )

    out_reservation_color = fields.Char(
        string="Checkout",
        help="Color for done not paid reservations in the planning.",
        default="rgba(88,77,118)",
    )

    staff_reservation_color = fields.Char(
        string="Staff",
        help="Color for staff reservations in the planning.",
        default="rgba(192,134,134)",
    )

    to_assign_reservation_color = fields.Char(
        string="OTA Reservation To Assign",
        help="Color for to_assign reservations in the planning.",
        default="rgba(237,114,46,)",
    )

    pending_payment_reservation_color = fields.Char(
        string="Payment Pending",
        help="Color for pending payment reservations in the planning.",
        default="rgba(162,70,137)",
    )

    availability_rule_field_ids = fields.Many2many(
        string="Availability Rules",
        help="Configurable availability rules",
        default=lambda x: x._get_default_avail_rule_fields(),
        comodel_name="ir.model.fields",
        relation="ir_model_fields_pms_property_rel",
        column1="ir_model_fields",
        column2="pms_property",

    )

    def _get_default_avail_rule_fields(self):
        avail_rule_fields = self.env['ir.model.fields'].search([('model_id', '=', 'pms.availability.plan.rule'), ('name', 'in', ('min_stay', 'quota'))])
        if avail_rule_fields:
            return avail_rule_fields.ids
        else:
            return []
