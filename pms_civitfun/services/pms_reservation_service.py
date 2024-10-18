import logging
from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

FORMAT_DATE = "%Y-%m-%d"


class CivitfunReservationService(Component):
    _inherit = "base.rest.service"
    _name = "civitfun.reservation.service"
    _usage = "bookings"
    _collection = "civitfun.services"

    # ------------------------------------------------------------------------------------
    # HEAD RESERVATION--------------------------------------------------------------------
    # ------------------------------------------------------------------------------------

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("civitfun.reservation.search.info", is_list=False),
        output_param=Datamodel("civitfun.booking.results", is_list=False),
        auth="public",
    )
    def get_reservations(self, pms_search_param):
        try:
            pms_property = (
                self.env["pms.property"]
                .sudo()
                .search([("civitfun_property_code", "=", pms_search_param.propertyId)])
            )
            if not pms_property:
                raise MissingError(_("Property not found"))
            domain = [
                ("pms_property_id", "=", pms_property.id),
                ("state", "in", ["draft", "confirm", "done"]),
                ("reservation_type", "!=", "out"),
            ]
            if pms_search_param.bookingIdentifier:
                booking_identifier = pms_search_param.bookingIdentifier.replace(
                    "-", "/"
                )
                domain.append(("name", "=", booking_identifier))
            if pms_search_param.bookingCode:
                booking_code = pms_search_param.bookingCode.replace("-", "/")
                domain.extend(
                    [
                        "|",
                        "|",
                        ("external_reference", "=", booking_code),
                        ("name", "=", booking_code),
                        ("folio_id.name", "=", booking_code),
                    ]
                )
            if pms_search_param.entranceDate:
                domain.append(
                    (
                        "checkin",
                        "=",
                        datetime.strptime(
                            pms_search_param.entranceDate, "%Y-%m-%d"
                        ).date(),
                    )
                )
            if pms_search_param.departureDate:
                domain.append(
                    (
                        "checkout",
                        "=",
                        datetime.strptime(
                            pms_search_param.departureDate, "%Y-%m-%d"
                        ).date(),
                    )
                )
            if pms_search_param.bookingDate:
                domain.append(
                    (
                        "create_date",
                        ">=",
                        datetime.strptime(
                            pms_search_param.bookingDate, "%Y-%m-%d"
                        ).date(),
                    )
                )
            reservations = self.env["pms.reservation"].sudo().search(domain)
            bookings = []
            for reservation in reservations:
                bookings.append(self._mapped_reservation_info(reservation))
            if not bookings:
                raise MissingError(_("No bookings found"))
            bookingResult = self.env.datamodels["civitfun.booking.results"]
            return bookingResult(
                success=True,
                message="Booking ready to save guest data",
                bookings=bookings,
            )
        except Exception as e:
            bookingResult = self.env.datamodels["civitfun.booking.results"]
            return bookingResult(
                success=False,
                message=str(e),
                bookings=[],
            )

    def _mapped_reservation_info(self, reservation):
        """
        Transform a reservation into a civitfun.reservation.info datamodel
        """
        room = reservation.reservation_line_ids[0].room_id
        return self.env.datamodels["civitfun.reservation.info"](
            bookingIdentifier=reservation.name.replace("/", "-"),
            bookingCode=reservation.folio_id.external_reference or None,
            status=self._get_mapped_state(reservation.state),
            holder=reservation.partner_name,  # TODO: transform to civitfun format
            holderCountry=reservation.partner_id.country_id.code_alpha3
            if reservation.partner_id.country_id
            else None,
            email=reservation.email or None,
            entrance=reservation.checkin.strftime(FORMAT_DATE),
            entranceTime=reservation.arrival_hour or None,
            departure=reservation.checkout.strftime(FORMAT_DATE),
            departureTime=reservation.departure_hour or None,
            adults=reservation.adults,
            babies=0,
            children=reservation.children,
            regimeStay=reservation.board_service_room_id.pms_board_service_id.name
            or None,
            agency=reservation.agency_id.name or None,
            stayAmount=reservation.folio_id.amount_total,
            depositAmount=reservation.folio_pending_amount,
            customerNotes=reservation.partner_requests or None,
            roomTypes=[
                {
                    "id": str(reservation.room_type_id.id),
                    "name": reservation.room_type_id.name,
                    "assignedRoom": {
                        "id": str(room.id),
                        "name": room.name,
                    },
                    "capacity": room.capacity,
                    "emptySlot": len(
                        reservation.checkin_partner_ids.filtered(
                            lambda x: x.state in ["dummy", "draft"]
                        )
                    ),
                }
            ],
            reallocationPropertyId=None,
            additionalInfo=[],
            guestsFilled=False,
            guests=self._mapped_guests(reservation),
        )

    def _mapped_guests(self, reservation):
        guests = []
        PmsCheckinPartner = self.env.datamodels["civitfun.checkin.partner.info"]
        for checkin in reservation.checkin_partner_ids:
            guests.append(
                PmsCheckinPartner(
                    id=str(checkin.id),
                    position=reservation.checkin_partner_ids.ids.index(checkin.id) + 1,
                    email=checkin.email or None,
                    lang=checkin.partner_id.lang or None,
                    language=checkin.partner_id.lang or None,
                    name=checkin.firstname or None,
                    surname=checkin.lastname or None,
                    secondSurname=checkin.lastname2 or None,
                    gender=self._get_mapped_gender(checkin.gender)
                    if checkin.gender
                    else None,
                    birthDate=checkin.birthdate_date.strftime(FORMAT_DATE)
                    if checkin.birthdate_date
                    else None,
                    nationality=checkin.nationality_id.code_alpha3 or None,
                    documentType=checkin.document_type.civitfun_category or None,
                    documentNumber=checkin.document_number or None,
                    expeditionDate=checkin.document_expedition_date.strftime(
                        FORMAT_DATE
                    )
                    if checkin.document_expedition_date
                    else None,
                )
            )
        return guests

    def _get_mapped_gender(self, gender):
        if gender == "male":
            return "M"
        if gender == "female":
            return "F"
        return "U"

    def _get_mapped_state(self, state):
        """
        Booking status
            ○ cancel -> canceled
            ○ / -> noShow
            ○ draft, confirm, arrival_delayed -> confirmed
            ○ onboard -> checkedIn
            ○ done, departure_delayed -> checkedOut
        """
        if state == "cancel":
            return "canceled"
        if state == "draft" or state == "confirm" or state == "arrival_delayed":
            return "confirmed"
        if state == "onboard":
            return "checkedIn"
        if state == "done" or state == "departure_delayed":
            return "checkedOut"
