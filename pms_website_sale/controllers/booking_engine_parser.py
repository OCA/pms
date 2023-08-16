# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta


class BookingEngineParser:
    def __init__(self, env):
        self.env = env
        self.booking_engine = None
        self.post_data = None

    def _get_booking_engine_vals(self):
        if self.post_data.get("start_date"):
            start_date = date.fromisoformat(self.post_data["start_date"])
        else:
            start_date = date.today()

        if self.post_data.get("end_date"):
            end_date = date.fromisoformat(self.post_data["end_date"])
        else:
            end_date = start_date + timedelta(days=1)

        partner = self.post_data.get("partner_id", False)
        if not partner:
            partner = self.env.ref("base.public_partner")

        online_channel = self.env.ref("pms_website_sale.online_channel")

        values = {
            "partner_id": partner.id,
            "start_date": start_date,
            "end_date": end_date,
            "channel_type_id": online_channel.id,
        }
        return values

    def _populate_availability_results(self):
        rooms_request = self.post_data.get("rooms_request", [])
        for room in rooms_request:
            room_availability = self.booking_engine.availability_results.filtered(
                lambda ar: ar.room_type_id.id == room["room_type_id"]
            )

            if not room_availability:
                raise ValueError(
                    "No room type for (%s, %s)"
                    % (room["room_type_id"], room["room_name"])
                )

            if room["quantity"] > room_availability.num_rooms_available:
                raise ValueError(
                    "Not enough rooms available"
                    " for (%s, %s)" % (room["room_type_id"], room["room_name"])
                )

            room_availability.value_num_rooms_selected = room["quantity"]

    def parse(self, post_data):
        self.post_data = post_data
        values = self._get_booking_engine_vals()
        self.booking_engine = (
            self.env["pms.booking.engine"]
            .sudo()  # fixme think this sudo
            .create(values)
        )
        self._populate_availability_results()
        return self.booking_engine
