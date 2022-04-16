# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector_pms.components.adapter import ChannelAdapterError
from odoo.addons.connector_pms_wubook.models.pms_reservation.mapper_import import (
    get_room_type,
)


class ChannelWubookPmsFolioAdapter(Component):
    _name = "channel.wubook.pms.folio"
    _inherit = "channel.wubook.adapter"

    _apply_on = "channel.wubook.pms.folio"

    _id = "reservation_code"

    # CRUD
    # pylint: disable=W8106
    def create(self, values):
        """
        * new_reservation(token, lcode, dfrom, dto, rooms, customer,
               amount[, origin= 'xml', ccard= 0, ancillary= 0, guests= 0,
               ignore_restrs= 0, ignore_avail= 0])
           https://tdocs.wubook.net/wired/rsrvs.html#new_reservation
        """
        raise ChannelAdapterError(_("Create reservations is currently not supported"))

    def read(self, _id, ancillary=True):
        """
        * fetch_booking(token, lcode, rcode[, ancillary= False])
           https://tdocs.wubook.net/wired/fetch.html#fetch_booking
        """
        kw_params = {
            "rcode": _id,
        }
        if ancillary:
            kw_params["ancillary"] = 1
        params = self._prepare_parameters(kw_params, ["rcode"], ["ancillary"])
        values = self._exec("fetch_booking", *params)
        self._format_folio_data(values)
        self._reorg_folio_data(values)
        if not values:
            return False
        return values[0]

    # flake8: noqa=C901
    def search_read(self, domain, ancillary=True, mark=False, only_codes=False):
        """
        * fetch_new_bookings(token, lcode[, ancillary=0, mark=1])
           https://tdocs.wubook.net/wired/fetch.html#fetch_new_bookings

        * fetch_bookings(token, lcode[, dfrom= None, dto= None, oncreated= 1,
                                        ancillary= 0])
           https://tdocs.wubook.net/wired/fetch.html#fetch_bookings
           If not filter (dfrom and dto) is specified, this call will be equal
           to a fetch_new_bookings() call, with mark parameter = 1.

        * fetch_bookings_codes(token, lcode, dfrom, dto[, oncreated= 1])
           https://tdocs.wubook.net/wired/fetch.html#fetch_bookings_codes

        * fetch_booking(token, lcode, rcode[, ancillary= False])
           https://tdocs.wubook.net/wired/fetch.html#fetch_booking
        """
        # TODO: refactor, split into smaller methods
        kw_params = {}
        date_field = "date_arrival"
        domain_date, domain = self._extract_domain_clauses(domain, date_field)
        if domain_date:
            kw_params["oncreated"] = 0
            if self._extract_domain_clauses(domain, "date_received_time")[0]:
                raise ValidationError(
                    _("Only allowed 'date_arrival' or 'date_received_time' not both")
                )
        else:
            date_field = "date_received_time"
            domain_date, domain = self._extract_domain_clauses(domain, date_field)
        if domain_date:
            kw_params = {
                **kw_params,
                **self._domain_to_normalized_dict(domain_date, date_field),
            }
            date_field_args = [("%s_%%s" % date_field) % x for x in ["from", "to"]]
            if only_codes:
                params = self._prepare_parameters(
                    kw_params, date_field_args, ["oncreated"]
                )
                values = self._exec("fetch_bookings_codes", *params)
            else:
                if ancillary:
                    kw_params["ancillary"] = 1
                params = self._prepare_parameters(
                    kw_params, [], date_field_args + ["oncreated", "ancillary"]
                )
                values = self._exec("fetch_bookings", *params)
            if mark:
                reservation_codes = [x[self._id] for x in values]
                self.write(
                    reservation_codes,
                    {
                        "mark": 1,
                    },
                )
        else:
            if ancillary:
                kw_params["ancillary"] = 1
            reservation_codes = None
            if domain:
                domain_code = self._extract_domain_clauses(domain, self._id)[0]
                if domain_code:
                    code_d = (self._domain_to_normalized_dict(domain_code),)
                    reservation_codes = code_d.get(self._id)
            if reservation_codes:
                if not isinstance(reservation_codes, (tuple, list)):
                    reservation_codes = [reservation_codes]
                values = []
                for rcode in reservation_codes:
                    value = self.read(rcode, ancillary=ancillary)
                    if value:
                        values.append(value)
                if mark:
                    self.write(
                        reservation_codes,
                        {
                            "mark": 1,
                        },
                    )
            else:
                kw_params["mark"] = mark and 1 or 0
                params = self._prepare_parameters(kw_params, [], ["ancillary", "mark"])
                # cycle call, 120 for each call, with mark=1
                # otherwise it goes to infinite loop
                values = []
                while True:
                    value = self._exec("fetch_new_bookings", *params)
                    values += value
                    if not value or not mark:
                        break

        self._format_folio_data(values)
        values = self._filter(values, domain)
        self._reorg_folio_data(values)

        return values

    def search(self, domain):
        values = self.search_read(domain)
        ids = [x[self._id] for x in values]
        return ids

    # pylint: disable=W8106
    def write(self, _ids, values):
        """
        * mark_bookings(token, lcode, reservations)
           https://tdocs.wubook.net/wired/fetch.html#mark_bookings
        * cancel_reservation(token, lcode, rcode[, reason= '', send_voucher= 1])
           https://tdocs.wubook.net/wired/rsrvs.html#cancel_reservation
        * confirm_reservation(token, lcode, rcode[, reason= '', send_voucher= 1])
           https://tdocs.wubook.net/wired/rsrvs.html#confirm_reservation
        * reconfirm_reservation(token, lcode, rcode[, reason= '', send_voucher= 1])
           https://tdocs.wubook.net/wired/rsrvs.html#reconfirm_reservation
        """
        if not isinstance(_ids, (tuple, list)):
            _ids = [_ids]

        # plan values
        if _ids:
            if "mark" in values:
                if values["mark"] == 1:
                    params = self._prepare_parameters(
                        {"reservations": _ids},
                        ["reservations"],
                    )
                    self._exec("mark_bookings", *params)

    def delete(self, _id):
        raise ChannelAdapterError(_("Reservations cannot be deleted"))

    # MISC
    def push_activation(self, url, test=0):
        """
        https://tdocs.wubook.net/wired/fetch.html#push_activation
        """
        params = self._prepare_parameters({"url": url, "test": test}, ["url"], ["test"])
        self._exec("push_activation", *params)

    def push_url(self):
        """
        https://tdocs.wubook.net/wired/fetch.html#push_url
        """
        url = self._exec("push_url")
        return url

    # aux
    def _format_folio_data(self, values):
        # https://tdocs.wubook.net/wired/fetch.html#reservation-representations
        conv_mapper = {
            "/dayprices": lambda x: int(x),
            "/rooms": lambda x: [int(x) for x in x.split(",")],
            "/date_received_time": lambda x: datetime.datetime.strptime(
                x, "%s %%H:%%M:%%S" % self._date_format
            ),
            "/booked_rooms/roomdays/day": lambda x: datetime.datetime.strptime(
                x, self._date_format
            ).date(),
            "/date_departure": lambda x: datetime.datetime.strptime(
                x, self._date_format
            ).date(),
            "/date_arrival": lambda x: datetime.datetime.strptime(
                x, self._date_format
            ).date(),
            "/arrival_hour": lambda x: x != "--" and x or None,
            "/boards": lambda x: int(x),
            # "/roomnight": lambda x: REMOVE_STRING, # deprecated
            # "/date_received": lambda x: REMOVE_STRING,  # deprecated
            # "/deleted_at": lambda x: REMOVE_STRING,  # deprecated
        }
        self._convert_format(values, conv_mapper)

    def _reorg_folio_data(self, values):
        # reorganize data
        for value in values:
            # reservations
            occupancies_d = {
                x["id"]: x["occupancy"] for x in value.pop("rooms_occupancies")
            }
            boards_d = {}
            boards = value.pop("boards")
            if boards:
                boards_d = {k: v != "nb" and v or None for k, v in boards.items()}

            channel_data = value.get("channel_data")
            vat_included = channel_data.get("vat_included", True)
            id_channel = value["id_channel"]

            customer_notes = value.pop("customer_notes")
            reservations = []
            for room in value.pop("booked_rooms"):
                room_id = room["room_id"]
                # If not occupancies in values set the default occupancy
                # with the min occupancy of the room type
                if not occupancies_d:
                    import_mapper = self.component(usage="import.mapper")
                    room_type = get_room_type(import_mapper, room_id)
                    occupancies_d[room_id] = min(room_type.room_ids.mapped("capacity"))
                # TODO: move the following code to method and
                #  remove boards_d
                board = boards_d.get(room_id)
                if id_channel == 2: # Booking.com
                    # Board services can be included in the rate
                    # plan and detected by the WuBook API
                    detected_board = value.get("ancillary", {}).get("Detected Board")
                    board = detected_board != "nb" and detected_board or None
                    # Guests can differ from the Wubook ones???
                    guests = room.get("ancillary", {}).get("guests")
                    if guests:
                        occupancies_d[room_id] = min(occupancies_d[room_id], guests)

                lines = []
                room_rate_id = None
                for days in room["roomdays"]:
                    rate_id = (
                        days["rate_id"] or self.backend_record.pricelist_external_id
                    )
                    if room_rate_id is None:
                        room_rate_id = rate_id
                    else:
                        if room_rate_id != rate_id:
                            raise ValidationError(
                                _("Found different pricelists on the same reservation")
                            )
                    lines.append(
                        {
                            "ancillary": days["ancillary"],
                            "price": days["price"],
                            "day": days["day"],
                            "room_id": room_id,
                            "board": board,
                            "occupancy": occupancies_d.get(room_id) or 1,
                            "board_included": id_channel != 0,
                            "vat_included": vat_included,
                        }
                    )

                reservations.append(
                    {
                        "room_id": room_id,
                        "arrival_hour": value["arrival_hour"],
                        "ota_reservation_code": value["channel_reservation_code"],
                        "board": board,
                        "occupancy": occupancies_d[room_id],
                        "rate_id": room_rate_id,
                        "customer_notes": customer_notes,
                        "lines": lines,
                    }
                )
            value["reservations"] = reservations
        return values
