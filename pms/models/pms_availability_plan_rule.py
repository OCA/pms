# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsAvailabilityPlanRule(models.Model):
    _name = "pms.availability.plan.rule"
    _description = "Reservation rule by day"
    _check_pms_properties_auto = True

    availability_plan_id = fields.Many2one(
        string="Availability Plan",
        help="The availability plan that include the Availabilty Rule",
        index=True,
        comodel_name="pms.availability.plan",
        ondelete="cascade",
        check_pms_properties=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room type for which availability rule is applied",
        required=True,
        comodel_name="pms.room.type",
        ondelete="cascade",
        check_pms_properties=True,
    )
    date = fields.Date(
        string="Date",
        help="Date for which availability rule applies",
    )

    min_stay = fields.Integer(
        string="Min. Stay",
        help="Minimum stay",
        default=0,
    )
    min_stay_arrival = fields.Integer(
        string="Min. Stay Arrival",
        help="Minimum stay if checkin is today",
        default=0,
    )
    max_stay = fields.Integer(
        string="Max. Stay",
        help="Maximum stay",
        default=0,
    )
    max_stay_arrival = fields.Integer(
        string="Max. Stay Arrival",
        help="Maximum stay if checkin is today",
        default=0,
    )
    closed = fields.Boolean(
        string="Closed",
        help="Indicate if property is closed or not",
        default=False,
    )
    closed_departure = fields.Boolean(
        string="Closed Departure",
        help="",
        default=False,
    )
    closed_arrival = fields.Boolean(
        string="Closed Arrival",
        help="",
        default=False,
    )
    quota = fields.Integer(
        string="Quota",
        help="Generic Quota assigned.",
        readonly=False,
        store=True,
        compute="_compute_quota",
    )
    max_avail = fields.Integer(
        string="Max. Availability",
        help="Maximum simultaneous availability on own Booking Engine",
        readonly=False,
        store=True,
        compute="_compute_max_avail",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element",
        ondelete="restrict",
        required=True,
        comodel_name="pms.property",
        check_pms_properties=True,
    )
    avail_id = fields.Many2one(
        string="Avail record",
        comodel_name="pms.availability",
        compute="_compute_avail_id",
        store=True,
        readonly=False,
        ondelete="restrict",
        check_pms_properties=True,
    )
    real_avail = fields.Integer(
        string="Real availability",
        related="avail_id.real_avail",
        store="True",
    )
    plan_avail = fields.Integer(
        compute="_compute_plan_avail",
        store="True",
    )

    _sql_constraints = [
        (
            "room_type_registry_unique",
            "unique(availability_plan_id, room_type_id, date, pms_property_id)",
            "Only can exists one availability rule in the same \
                         day for the same room type!",
        )
    ]

    @api.depends("room_type_id", "date", "pms_property_id")
    def _compute_avail_id(self):
        for record in self:
            if record.room_type_id and record.pms_property_id and record.date:
                avail = self.env["pms.availability"].search(
                    [
                        ("date", "=", record.date),
                        ("room_type_id", "=", record.room_type_id.id),
                        ("pms_property_id", "=", record.pms_property_id.id),
                    ]
                )
                if avail:
                    record.avail_id = avail.id
                else:
                    record.avail_id = self.env["pms.availability"].create(
                        {
                            "date": record.date,
                            "room_type_id": record.room_type_id.id,
                            "pms_property_id": record.pms_property_id.id,
                        }
                    )
            else:
                record.avail_id = False

    @api.depends("quota", "max_avail", "real_avail")
    def _compute_plan_avail(self):
        for record in self.filtered("real_avail"):
            real_avail = record.real_avail
            plan_avail = min(
                [
                    record.max_avail if record.max_avail >= 0 else real_avail,
                    record.quota if record.quota >= 0 else real_avail,
                    real_avail,
                ]
            )
            if not record.plan_avail or record.plan_avail != plan_avail:
                record.plan_avail = plan_avail

    @api.depends("room_type_id")
    def _compute_quota(self):
        for record in self:
            if not record.quota:
                record.quota = record.room_type_id.default_quota

    @api.depends("room_type_id")
    def _compute_max_avail(self):
        for record in self:
            if not record.max_avail:
                record.max_avail = record.room_type_id.default_max_avail

    @api.constrains("min_stay", "min_stay_arrival", "max_stay", "max_stay_arrival")
    def _check_min_max_stay(self):
        for record in self:
            if record.min_stay < 0:
                raise ValidationError(_("Min. Stay can't be less than zero"))
            elif record.min_stay_arrival < 0:
                raise ValidationError(_("Min. Stay Arrival can't be less than zero"))
            elif record.max_stay < 0:
                raise ValidationError(_("Max. Stay can't be less than zero"))
            elif record.max_stay_arrival < 0:
                raise ValidationError(_("Max. Stay Arrival can't be less than zero"))
            elif (
                record.min_stay != 0
                and record.max_stay != 0
                and record.min_stay > record.max_stay
            ):
                raise ValidationError(_("Max. Stay can't be less than Min. Stay"))
            elif (
                record.min_stay_arrival != 0
                and record.max_stay_arrival != 0
                and record.min_stay_arrival > record.max_stay_arrival
            ):
                raise ValidationError(
                    _("Max. Stay Arrival can't be less than Min. Stay Arrival")
                )
