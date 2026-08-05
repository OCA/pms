from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsCheckinPartnerUnaccompaniedMinors(TestPms):
    """The unaccompanied minors declaration is scoped to the folio.

    The party is not split by room: the guardians may be booked in one
    reservation and the minors in another one of the same folio.
    """

    def setUp(self):
        super().setUp()
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room type test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        self.room_1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 1",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.room_2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 2",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.today = fields.Date.today()

    def _birthdate_for_age(self, years):
        return self.today - relativedelta(years=years)

    def _create_reservation(self, room, folio=None):
        vals = {
            "pms_property_id": self.pms_property1.id,
            "room_type_id": self.room_type.id,
            "preferred_room_id": room.id,
            "checkin": self.today,
            "checkout": self.today + relativedelta(days=2),
            "adults": 1,
            "sale_channel_origin_id": self.sale_channel_direct1.id,
            "partner_name": "Test reservation",
        }
        if folio:
            vals["folio_id"] = folio.id
        return self.env["pms.reservation"].create(vals)

    def _create_folio_with_two_rooms(self, first_age, second_age):
        """Two reservations in the same folio, one guest each."""
        first_reservation = self._create_reservation(self.room_1)
        second_reservation = self._create_reservation(
            self.room_2, folio=first_reservation.folio_id
        )
        first_guest = first_reservation.checkin_partner_ids[0]
        second_guest = second_reservation.checkin_partner_ids[0]
        first_guest.birthdate_date = (
            self._birthdate_for_age(first_age) if first_age else False
        )
        second_guest.birthdate_date = (
            self._birthdate_for_age(second_age) if second_age else False
        )
        return first_reservation, second_reservation

    def test_all_guests_minors_when_every_guest_of_the_folio_is_under_age(self):
        # ARRANGE / ACT
        first_reservation, _second = self._create_folio_with_two_rooms(16, 14)
        # ASSERT
        self.assertTrue(
            first_reservation.folio_id.ses_all_guests_minors,
            "A folio whose every guest is under age should be flagged as "
            "having only minors",
        )

    def test_not_all_guests_minors_when_the_guest_of_age_is_in_another_room(self):
        # ARRANGE / ACT
        # The guardians in one reservation and the minor in another one: the
        # minor's own reservation holds nothing but a minor.
        minors_reservation, _guardians = self._create_folio_with_two_rooms(16, 40)
        # ASSERT
        self.assertFalse(
            minors_reservation.folio_id.ses_all_guests_minors,
            "A guest of age in another reservation of the folio should count",
        )

    def test_all_guests_minors_ignores_the_guests_with_no_birthdate(self):
        # ARRANGE / ACT
        # An unfilled guest slot elsewhere in the folio must not hide the
        # declaration: the checkin data gets filled in any order.
        first_reservation, _second = self._create_folio_with_two_rooms(16, None)
        # ASSERT
        self.assertTrue(
            first_reservation.folio_id.ses_all_guests_minors,
            "Guests with no birthdate yet should not be taken into account",
        )

    def test_guest_of_age_in_a_cancelled_reservation_is_ignored(self):
        # ARRANGE
        minors_reservation, guardians_reservation = self._create_folio_with_two_rooms(
            16, 40
        )
        # ACT
        guardians_reservation.action_cancel()
        # ASSERT
        self.assertTrue(
            minors_reservation.folio_id.ses_all_guests_minors,
            "Guests of a cancelled reservation are not part of the party",
        )

    def test_minor_requires_relationship_when_accompanied(self):
        # ARRANGE
        reservation = self._create_reservation(self.room_1)
        checkin_partner = reservation.checkin_partner_ids[0]
        checkin_partner.birthdate_date = self._birthdate_for_age(16)
        # ACT
        mandatory_fields = checkin_partner._checkin_mandatory_fields()
        # ASSERT
        self.assertIn(
            "ses_partners_relationship",
            mandatory_fields,
            "A minor should require the relationship with another guest",
        )
        self.assertIn(
            "ses_related_checkin_partner_id",
            mandatory_fields,
            "A minor should require the guest they are related to",
        )

    def test_minor_does_not_require_relationship_when_unaccompanied(self):
        # ARRANGE
        reservation = self._create_reservation(self.room_1)
        # Declared through the reservation on purpose: that is where it gets
        # managed, even though it is stored on the folio.
        reservation.ses_unaccompanied_minors = True
        checkin_partner = reservation.checkin_partner_ids[0]
        checkin_partner.birthdate_date = self._birthdate_for_age(16)
        # ASSERT
        self.assertTrue(
            reservation.folio_id.ses_unaccompanied_minors,
            "Declaring it on the reservation should store it on the folio",
        )
        mandatory_fields = checkin_partner._checkin_mandatory_fields()
        self.assertNotIn(
            "ses_partners_relationship",
            mandatory_fields,
            "An unaccompanied minor should not require the relationship with "
            "another guest",
        )
        self.assertNotIn(
            "ses_related_checkin_partner_id",
            mandatory_fields,
            "An unaccompanied minor should not require the guest they are "
            "related to",
        )

    def test_unaccompanied_minors_blocked_by_a_guest_of_age_in_another_room(self):
        # ARRANGE
        # The minor boards first, and the guest of age is in another reservation
        # of the folio: the inconsistency must be caught all the same.
        minors_reservation, _guardians = self._create_folio_with_two_rooms(16, 40)
        minors_reservation.folio_id.ses_unaccompanied_minors = True
        minor = minors_reservation.checkin_partner_ids[0]
        # ACT / ASSERT
        # Matching the message on purpose: an incomplete checkin also raises
        # ValidationError from the mandatory fields, so asserting the exception
        # type alone would pass even without the consistency check.
        with self.assertRaisesRegex(ValidationError, "unaccompanied minors"):
            minor.action_on_board()

    def test_unaccompanied_minors_allowed_when_a_birthdate_is_missing(self):
        # ARRANGE
        # Nobody is known to be of age, so an incomplete folio must not be
        # reported as inconsistent.
        minors_reservation, _second = self._create_folio_with_two_rooms(16, None)
        minors_reservation.folio_id.ses_unaccompanied_minors = True
        # ACT / ASSERT
        minors_reservation.folio_id._check_ses_unaccompanied_minors()
