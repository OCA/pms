from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SeveralPartners(models.TransientModel):
    _name = "pms.several.partners.wizard"
    _description = "Partner Operations"

    reservation_id = fields.Many2one(
        string="Reservation",
        comodel_name="pms.reservation",
    )

    folio_id = fields.Many2one(
        string="Folio",
        comodel_name="pms.folio",
    )

    checkin_partner_id = fields.Many2one(
        string="Checkin Partner", comodel_name="pms.checkin.partner"
    )
    possible_existing_customer_ids = fields.Many2many(
        string="Customers", comodel_name="res.partner", store=True, readonly=False
    )

    @api.model
    def default_get(self, fields):
        res = super(SeveralPartners, self).default_get(fields)
        possibles_customers_ids = self.env["res.partner"].browse(
            self._context.get("possible_existing_customer_ids")
        )
        res.update({"possible_existing_customer_ids": possibles_customers_ids})
        reservation = self.env["pms.reservation"].browse(
            self._context.get("reservation_id")
        )
        if reservation:
            res.update(
                {
                    "reservation_id": reservation.id,
                }
            )
        folio = self.env["pms.folio"].browse(self._context.get("folio_id"))
        if folio:
            res.update(
                {
                    "folio_id": folio.id,
                }
            )
        checkin_partner = self.env["pms.checkin.partner"].browse(
            self._context.get("checkin_partner_id")
        )
        if checkin_partner:
            res.update(
                {
                    "checkin_partner_id": checkin_partner.id,
                }
            )
        return res

    def add_partner(self):
        for record in self:
            if len(record.possible_existing_customer_ids) == 0:
                raise ValidationError(
                    _(
                        "You must select a client to be able to add it to the reservation "
                    )
                )
            if len(record.possible_existing_customer_ids) > 1:
                raise ValidationError(
                    _("Only one customer can be added to the reservation")
                )
            if record.reservation_id:
                record.reservation_id.partner_id = record.possible_existing_customer_ids
            elif record.folio_id:
                record.folio_id.partner_id = record.possible_existing_customer_ids
            elif record.checkin_partner_id:
                record.checkin_partner_id.partner_id = (
                    record.possible_existing_customer_ids
                )
