# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta


class BookingEngineParser:
    SESSION_KEY = "booking_engine_data"

    def __init__(self, env, session):
        self._session = session
        self.env = env
        self.data = self._session.get(BookingEngineParser.SESSION_KEY, {})
        self._init_data()
        self.booking_engine = None

    @staticmethod
    def _check_daterange(start_date, end_date):
        if (start_date and not end_date) or (not start_date and end_date):
            raise ValueError(
                "Date range is not correct: from %s to %s" % (start_date, end_date)
            )
        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date must be before the end date")

    def _init_data(self):
        """Init some value of data"""
        if "rooms_requests" not in self.data:
            self.data["rooms_requests"] = []

    def _get_booking_engine_vals(self):
        # FIXME: does not allow to show all rooms when no date range
        # is selected.
        if self.data.get("start_date"):
            start_date = date.fromisoformat(self.data["start_date"])
        else:
            start_date = date.today()

        if self.data.get("end_date"):
            end_date = date.fromisoformat(self.data["end_date"])
        else:
            end_date = start_date + timedelta(days=1)

        partner = (
            self.env["res.partner"].browse(self.data.get("partner_id", False)).exists()
        )
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
        rooms_requests = self.data.get("rooms_requests", [])
        for room in rooms_requests:
            room_availability = self.booking_engine.availability_results.filtered(
                lambda ar: ar.room_type_id.id == room["room_type_id"]
            )

            if not room_availability:
                raise ValueError(
                    "No room type for room ID: %s" % (room["room_type_id"])
                )

            if room["quantity"] > room_availability.num_rooms_available:
                raise ValueError(
                    "Not enough rooms available"
                    " for (%s, %s)"
                    % (room["room_type_id"], room_availability.room_type_id.name)
                )

            room_availability.value_num_rooms_selected = room["quantity"]

    def _get_room_request(self, room_type_id):
        """Return (first) room request that match room_type_id"""
        for room_request in self.data.get("rooms_requests", []):
            if room_request["room_type_id"] == room_type_id:
                return room_request
        return None

    def parse(self):
        """Create a booking.engine based on the parser data"""
        values = self._get_booking_engine_vals()
        self.booking_engine = self.env["pms.booking.engine"].sudo().create(values)
        self._populate_availability_results()
        return self.booking_engine

    def save(self):
        """Save data into session"""
        self._session[BookingEngineParser.SESSION_KEY] = self.data

    def set_daterange(self, start_date, end_date, overwrite=True):
        """Set a start_date and a end_date for booking"""
        if (
            not self.data.get("start_date")
            and not self.data.get("end_date")
            or overwrite
        ):
            BookingEngineParser._check_daterange(start_date, end_date)
            self.data["start_date"] = str(start_date) if start_date else None
            self.data["end_date"] = str(end_date) if end_date else None

    def add_room_request(self, room_type_id, quantity, start_date=None, end_date=None):
        """Add or update a room request to the booking"""
        # FIXME: Perhaps this method should be renamed
        # `update_room_request` because it also update records when a
        # record already exists. Or it can be split into two function.
        # An idea can be also to merge `del_room_request` and
        # `add_room_request` into `update_room_request` where the
        # deletion is performed when quantity is null.
        # To be discussed.
        if start_date != self.data.get("start_date") or end_date != self.data.get(
            "end_date"
        ):
            ValueError(
                "Booking date does not match existing booking date. "
                "The room cannot be booked."
            )
        try:
            room_type_id = int(room_type_id)
            quantity = int(quantity)
        except (ValueError, TypeError):
            raise ValueError("Cannot proceed due to incorrect value.")

        new_room_request = {
            "room_type_id": room_type_id,
            "quantity": quantity,
        }
        existing_room_request = self._get_room_request(room_type_id)
        if existing_room_request:
            existing_room_request.update(new_room_request)
        else:
            self.data["rooms_requests"].append(new_room_request)

    def del_room_request(self, room_type_id):
        """Remove a room request to the booking"""
        try:
            room_type_id = int(room_type_id)
        except (ValueError, TypeError):
            raise ValueError("Cannot proceed due to incorrect value")
        del_index = None
        for index, room_request in enumerate(self.data["rooms_requests"]):
            if room_request.get("room_type_id") == room_type_id:
                del_index = index
        if del_index is not None:
            self.data["rooms_requests"].pop(del_index)
        # FIXME: should we report error when trying to delete a non
        # existing room to end user ?
