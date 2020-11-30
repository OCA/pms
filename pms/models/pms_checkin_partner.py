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
    identifier = fields.Char(
        "Identifier",
        compute="_compute_identifier",
        readonly=False,
        store=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        domain="[('is_company', '=', False)]",
    )
    reservation_id = fields.Many2one("pms.reservation")
    folio_id = fields.Many2one(
        "pms.folio",
        compute="_compute_folio_id",
        store=True,
    )
    pms_property_id = fields.Many2one(
        "pms.property", default=_get_default_pms_property, required=True
    )
    name = fields.Char("Name", related="partner_id.name")
    email = fields.Char("E-mail", related="partner_id.email")
    mobile = fields.Char("Mobile", related="partner_id.mobile")
    image_128 = fields.Image(related="partner_id.image_128")
    segmentation_ids = fields.Many2many(
        related="reservation_id.segmentation_ids",
        readonly=True,
    )
    arrival = fields.Datetime("Enter")
    departure = fields.Datetime("Exit")
    state = fields.Selection(
        selection=[
            ("draft", "Unkown Guest"),
            ("precheckin", "Pending arrival"),
            ("onboard", "On Board"),
            ("done", "Out"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        compute="_compute_state",
        store=True,
        readonly=True,
    )

    # Compute
    @api.depends("reservation_id", "folio_id", "reservation_id.preferred_room_id")
    def _compute_identifier(self):
        for record in self:
            # TODO: Identifier
            checkins = []
            if record.reservation_id.filtered("preferred_room_id"):
                checkins = record.reservation_id.checkin_partner_ids
                record.identifier = (
                    record.reservation_id.preferred_room_id.name
                    + "-"
                    + str(len(checkins) - 1)
                )
            elif record.folio_id:
                record.identifier = record.folio_id.name + "-" + str(len(checkins) - 1)
            else:
                record.identifier = False

    @api.depends("reservation_id", "reservation_id.folio_id")
    def _compute_folio_id(self):
        for record in self.filtered("reservation_id"):
            record.folio_id = record.reservation_id.folio_id

    @api.depends(lambda self: self._checkin_mandatory_fields(depends=True))
    def _compute_state(self):
        for record in self:
            if not record.state:
                record.state = "draft"
            if record.reservation_id.state == "cancelled":
                record.state = "cancelled"
            elif record.state in ("draft", "cancelled"):
                if any(
                    not getattr(record, field)
                    for field in record._checkin_mandatory_fields()
                ):
                    record.state = "draft"
                else:
                    record.state = "precheckin"

    @api.model
    def _checkin_mandatory_fields(self, depends=False):
        # api.depends need "reservation_id.state" in de lambda function
        if depends:
            return ["reservation_id.state", "name"]
        return ["name"]

    # Constraints and onchanges

    @api.constrains("departure", "arrival")
    def _check_departure(self):
        for record in self:
            if record.departure and record.arrival > record.departure:
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

    # CRUD
    @api.model
    def create(self, vals):
        # The checkin records are created automatically from adult depends
        # if you try to create one manually, we update one unassigned checkin
        if not self._context.get("auto_create_checkin"):
            reservation_id = vals.get("reservation_id")
            if reservation_id:
                reservation = self.env["pms.reservation"].browse(reservation_id)
                draft_checkins = reservation.checkin_partner_ids.filtered(
                    lambda c: c.state == "draft"
                )
                if len(draft_checkins) > 0 and vals.get("partner_id"):
                    draft_checkins[0].sudo().unlink()
        return super(PmsCheckinPartner, self).create(vals)

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
            if record.reservation_id.left_for_checkin:
                record.reservation_id.state = "onboard"

    def action_done(self):
        for record in self.filtered(lambda c: c.state == "onboard"):
            vals = {
                "state": "done",
                "departure": fields.Datetime.now(),
            }
            record.update(vals)
        return True
