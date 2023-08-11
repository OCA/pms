# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo import _, fields, models


class BookingEngine(models.TransientModel):
    _inherit = "pms.booking.engine"

    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False)

    def create_folio(self):
        for engine in self:
            if not (engine.start_date and engine.end_date):
                raise ValueError(_("Start and end dates must be set to create a folio"))
        return super().create()

    def _compute_availability_results(self):
        """
        Computes availabilities for each room type do if dates are set
        otherwise returns a line with num_rooms_available = 0 for each room type
        :return:
        """
        for engine in self:
            engine.availability_results = False
            if engine.start_date and engine.end_date:
                super(BookingEngine, engine)._compute_availability_results()
            else:
                today = date.today()
                room_types = self.env["pms.room.type"].get_room_types_by_property(
                    engine.pms_property_id.id
                )

                availability_results = engine.availability_results
                for room_type in room_types:
                    availability_results |= availability_results.create(
                        {
                            "checkin": today,
                            "checkout": today + timedelta(days=1),
                            "room_type_id": room_type.id,
                            "pms_property_id": engine.pms_property_id.id,
                        }
                    )
                engine.availability_results = availability_results
