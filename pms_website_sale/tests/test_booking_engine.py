# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .pms_test_commons import PMSTestCommons


class BookingEngineCase(PMSTestCommons):
    def test_compute_availability_results_with_no_dates(self):
        engine = self.env["pms.booking.engine"].create(
            {
                "pms_property_id": self.property.id,
                "channel_type_id": self.online_channel.id,
            }
        )
        # only consider the rooms created in this case
        availabilities = engine.availability_results.filtered(
            lambda ar: ar.room_type_id in self.case_room_types
        )
        self.assertEqual(len(availabilities), 2)
        self.assertEqual(availabilities.mapped(lambda a: a.num_rooms_available), [0, 0])
