from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsFolio(models.Model):
    _inherit = "pms.folio"

    ses_all_guests_minors = fields.Boolean(
        string="All guests are minors",
        help="Every guest of the folio whose birthdate is known is under the "
        "age of majority.",
        compute="_compute_ses_all_guests_minors",
    )
    ses_unaccompanied_minors = fields.Boolean(
        string="Unaccompanied minors",
        help="The minors travel on their own with the authorization of their "
        "legal guardian. No relationship with an accompanying guest is "
        "required on their checkin data.",
        tracking=True,
    )
    ses_minors_authorization = fields.Binary(
        string="Guardian authorization",
        help="Authorization signed by the legal guardian of the minors.",
    )
    ses_minors_authorization_filename = fields.Char(
        string="Guardian authorization filename",
    )

    def _ses_staying_checkin_partners(self):
        """Guests of the folio that are actually staying.

        The guests are taken from the whole folio and not from a single
        reservation, because the party is not split by room: the guardians may
        be booked in one reservation and the minors in another one. Cancelled
        and out of service reservations are left out, since their guests are not
        part of the party the declaration talks about.
        """
        self.ensure_one()
        return self.checkin_partner_ids.filtered(
            lambda checkin_partner: checkin_partner.reservation_id.state != "cancel"
            and checkin_partner.reservation_id.reservation_type != "out"
        )

    @api.depends(
        "checkin_partner_ids.birthdate_date",
        "reservation_ids.state",
        "reservation_ids.reservation_type",
    )
    def _compute_ses_all_guests_minors(self):
        for record in self:
            # Guests with no birthdate yet are left out instead of blocking:
            # otherwise an unfilled guest slot anywhere in the folio would hide
            # the declaration, and the checkin data gets filled in any order.
            guests_with_birthdate = record._ses_staying_checkin_partners().filtered(
                "birthdate_date"
            )
            record.ses_all_guests_minors = bool(guests_with_birthdate) and all(
                checkin_partner._is_minor() for checkin_partner in guests_with_birthdate
            )

    def _check_ses_unaccompanied_minors(self):
        """Refuse an unaccompanied minors declaration that the guests contradict.

        Every guest of the folio is taken into account, no matter whether they
        already boarded, so the check does not depend on the order in which the
        guests are checked in. A guest with no birthdate yet is not known to be
        of age, so incomplete checkin data never raises here.
        """
        for record in self:
            if not record.ses_unaccompanied_minors:
                continue
            guests_of_age = record._ses_staying_checkin_partners().filtered(
                lambda checkin_partner: checkin_partner.birthdate_date
                and not checkin_partner._is_minor()
            )
            if guests_of_age:
                raise ValidationError(
                    _(
                        "%(guests)s is of age, so the unaccompanied minors "
                        "declaration of folio %(folio)s does not hold. Uncheck "
                        "the declaration or review the birthdates."
                    )
                    % {
                        "guests": ", ".join(guests_of_age.mapped("name")),
                        "folio": record.name,
                    }
                )
