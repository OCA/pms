# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Diaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsCheckinPartner(models.Model):
    _name = "pms.checkin.partner"
    _description = "Partner Checkins"

    @api.model
    def _get_default_pms_property(self):
        # TODO: Change by property env variable (like company)
        return self.env.user.pms_property_id

    # Fields declaration
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        domain="[('is_company', '=', False)]",
    )
    reservation_id = fields.Many2one("pms.reservation")
    folio_id = fields.Many2one(
        "pms.folio",
        compute="_compute_folio_id",
        store=True,
        readonly=False,
    )
    pms_property_id = fields.Many2one(
        "pms.property", default=_get_default_pms_property, required=True
    )
    email = fields.Char("E-mail", related="partner_id.email")
    mobile = fields.Char("Mobile", related="partner_id.mobile")
    arrival = fields.Datetime("Enter")
    departure = fields.Datetime("Exit")
    state = fields.Selection(
        selection=[
            ("draft", "Pending arrival"),
            ("onboard", "On Board"),
            ("done", "Out"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        readonly=True,
        default=lambda *a: "draft",
    )

    # Compute

    @api.depends("reservation_id", "reservation_id.folio_id")
    def _compute_folio_id(self):
        for record in self:
            record.folio_id = record.reservation_id.folio_id

    # Constraints and onchanges

    @api.constrains("departure", "arrival")
    def _check_departure(self):
        for record in self:
            if record.departure and record.arrival < record.departure:
                raise ValidationError(
                    _("Departure date (%s) is prior to arrival on %s")
                    % (record.departure, record.arrival)
                )

    @api.constrains("partner_id")
    def _check_partner_id(self):
        for record in self:
            if record.partner_id:
                indoor_partner_ids = record.reservation_id.checkin_partner_ids.filtered(
                    lambda r: r.id != record.id
                ).mapped("partner_id.id")
                if indoor_partner_ids.count(record.partner_id.id) > 1:
                    record.partner_id = None
                    raise ValidationError(
                        _("This guest is already registered in the room")
                    )

    # Action methods

    def action_on_board(self):
        for record in self:
            if record.reservation_id.checkin > fields.Date.today():
                raise ValidationError(_("It is not yet checkin day!"))
            if record.reservation_id.checkout <= fields.Date.today():
                raise ValidationError(_("Its too late to checkin"))
            vals = {
                "state": "onboard",
                "arrival": fields.Datetime.now(),
            }
            record.update(vals)
            if record.reservation_id.state == "confirm":
                record.reservation_id.state = "onboard"

    def action_done(self):
        for record in self:
            if record.state == "onboard":
                hour = record._get_departure_hour()
                vals = {
                    "state": "done",
                    "departure_hour": hour,
                }
                record.update(vals)
        return True
