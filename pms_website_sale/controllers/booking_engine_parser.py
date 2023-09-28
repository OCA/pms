# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date, timedelta

from odoo import _, tools


class ParserError(Exception):
    """Error containing two messages, a debugging message and a message
    to the end user.
    """

    def __init__(self, msg, usr_msg=None):
        self.usr_msg = usr_msg if usr_msg else msg
        super().__init__(msg)


class AvailabilityError(ParserError):
    """Error when a room is no more available"""

    def __init__(self, msg, usr_msg=None, room_type_id=None):
        super().__init__(msg, usr_msg=usr_msg)
        self.room_type_id = room_type_id


class AvailabilityErrorGroup(Exception):
    """Group multiple AvailabilityError in one Error"""

    def __init__(self, msg, excs):
        super().__init__(msg)
        self.excs = tuple(excs) if excs else tuple()


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
            raise ParserError(
                "Date range is not correct: from %s to %s" % (start_date, end_date)
            )
        if start_date and end_date and start_date > end_date:
            raise ParserError("Start date must be before the end date")

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
            "internal_comment": self.data.get("internal_comment", ""),
        }
        return values

    def _populate_availability_results(self):
        rooms_requests = self.data.get("rooms_requests", [])
        availability_errors = []
        for room in rooms_requests:
            room_availability = self.booking_engine.availability_results.filtered(
                lambda ar: ar.room_type_id.id == room["room_type_id"]
            )

            if not room_availability:
                raise ParserError(
                    "No room type for room ID: %s" % (room["room_type_id"])
                )

            if room["quantity"] > room_availability.num_rooms_available:
                room_type_id = room["room_type_id"]
                room_type_name = room_availability.room_type_id.name
                availability_errors.append(
                    AvailabilityError(
                        msg=(
                            f"Not enough rooms available for "
                            f"({room_type_id}, {room_type_name})"
                        ),
                        usr_msg=_(
                            "{name} rooms are not available anymore at selected dates."
                        ).format(name=room_type_name),
                        room_type_id=room_type_id,
                    )
                )
                room["quantity"] = 0

            room_availability.value_num_rooms_selected = room["quantity"]
        if availability_errors:
            raise AvailabilityErrorGroup(
                "Some rooms are not available anymore",
                availability_errors,
            )

    def _get_room_request(self, room_type_id):
        """Return (first) room request that match room_type_id"""
        for room_request in self.data.get("rooms_requests", []):
            if room_request["room_type_id"] == room_type_id:
                return room_request
        return None

    def _create_partner(self):
        """Create partner based on values in self.data"""
        try:
            partner_vals = {
                "name": self.data["partner"]["name"],
                "email": self.data["partner"]["email"],
                "mobile": self.data["partner"]["phone"],
                "street": self.data["partner"]["address"],
                "city": self.data["partner"]["city"],
                "zip": self.data["partner"]["postal_code"],
                "country_id": self.data["partner"]["country_id"],
            }
        except KeyError as err:
            raise ParserError(
                msg="Can not create partner: %s" % err,
                usr_msg="No value for contact person.",
            )
        partner = self.env["res.partner"].sudo().create(partner_vals)
        return partner

    def parse(self):
        """Create a booking.engine based on the parser data"""
        values = self._get_booking_engine_vals()
        self.booking_engine = self.env["pms.booking.engine"].sudo().create(values)
        self._populate_availability_results()
        return self.booking_engine

    def save(self):
        """Save data into session"""
        self._session[BookingEngineParser.SESSION_KEY] = self.data

    def reset(self):
        self.data = {}
        self._init_data()

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
            ParserError(
                "Booking date does not match existing booking date. "
                "The room cannot be booked."
            )
        try:
            room_type_id = int(room_type_id)
            quantity = int(quantity)
        except (ValueError, TypeError) as err:
            raise ParserError(
                msg=str(err), usr_msg="Cannot proceed due to incorrect value."
            )

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
        except (ValueError, TypeError) as err:
            raise ParserError(
                msg=str(err), usr_msg="Cannot proceed due to incorrect value."
            )
        if room_type_id not in (
            rr["room_type_id"] for rr in self.data["rooms_requests"]
        ):
            raise ParserError("There is no room with id %s." % room_type_id)
        self.data["rooms_requests"] = list(
            filter(
                lambda rr: rr["room_type_id"] != room_type_id,
                self.data["rooms_requests"],
            )
        )

    def create_folio(self):
        # FIXME: what to do if this function is called and that there is
        # no information about the partner recorded in the parser?
        # E.g.: The user has bypassed the address formular.
        folio_action = self.booking_engine.create_folio()
        folio = self.env["pms.folio"].browse(folio_action["res_id"])
        # we must assign the partner after folio creation because
        # setting the partner on the engine resets the room selection
        partner = self._create_partner()
        folio.sudo().partner_id = partner
        # do not return sudo folio
        return self.env["pms.folio"].browse(folio.id)

    def set_partner(
        self,
        name,
        email,
        phone,
        address,
        city,
        postal_code,
        country_id,
        accepted_terms_and_conditions,
    ):
        """Add partner values. Values should be clean."""
        if not name:
            raise ParserError("Name is required.")
        if not email:
            raise ParserError("Email is required.")
        if not phone:
            raise ParserError("Phone is required.")
        if not address:
            raise ParserError("Address is required.")
        if not city:
            raise ParserError("City is required.")
        if not postal_code:
            raise ParserError("Postal Code is required.")
        if not country_id:
            raise ParserError("Country is required.")
        if not accepted_terms_and_conditions:
            raise ParserError("You must accept terms and conditions.")

        if not tools.mail.single_email_re.match(email):
            raise ParserError("Email address is not valid.")

        try:
            country_id = int(country_id)
        except (ValueError, TypeError) as err:
            raise ParserError(msg=str(err), usr_msg="Incorrect value for Country.")

        country = self.env["res.country"].browse(country_id).exists()
        if not country:
            raise ParserError("Wrong value for Country")

        self.data["partner"] = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "postal_code": postal_code,
            "country_id": country_id,
            "accepted_terms_and_conditions": accepted_terms_and_conditions == "on",
        }

    def set_internal_comment(self, internal_comment):
        """Add internal comment to booking engine."""
        if not internal_comment:
            internal_comment = ""
        self.data["internal_comment"] = internal_comment
