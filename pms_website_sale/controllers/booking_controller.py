# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from werkzeug.exceptions import NotFound

from odoo import _, http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentProcessing

from .booking_engine_parser import (
    AvailabilityError,
    AvailabilityErrorGroup,
    BookingEngineParser,
    ParserError,
)

logger = logging.getLogger(__name__)


class BookingEngineController(http.Controller):
    @http.route(
        ["/ebooking/booking"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def booking(self, **kwargs):
        errors = []
        booking_engine = request.env["pms.booking.engine"]
        try:
            if request.httprequest.method == "GET":
                booking_engine = booking_engine = self._get_booking()
            elif request.httprequest.method == "POST":
                booking_engine = self._post_booking(**kwargs)
        except ParserError as e:
            logger.debug(e)
            errors.append(e.usr_msg)
        except KeyError as e:
            # FIXME: when does this type of error occur ?
            logger.error(e)
            errors.append("An unknown error occurs")
        except AvailabilityErrorGroup as e:
            logger.debug(e)
            for ae in e.excs:
                logger.debug(ae)
                errors.append(ae.usr_msg)
                self._process_availability_error(ae)

        values = {
            "booking_engine": booking_engine,
            "errors": errors,
        }
        return request.render("pms_website_sale.pms_booking_engine_page", values)

    @http.route(
        ["/ebooking/booking/extra_info"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def booking_extra_info(self, **kwargs):
        errors = []
        booking_engine = request.env["pms.booking.engine"]

        try:
            if request.httprequest.method == "POST":
                self._post_booking_extra_info(**kwargs)
                return request.redirect("/ebooking/booking/address")

            booking_engine = self._get_booking_extra_info()
        except ParserError as e:
            logger.debug(e)
            errors.append(e.usr_msg)
        except AvailabilityErrorGroup as e:
            return self._redirect_availability_error(e)

        # FIXME Is the booking engine really needed ?
        values = {
            "booking_engine": booking_engine,
            "notes": kwargs.get(
                "notes",
                booking_engine.internal_comment,
            ),
            "errors": errors,
        }
        return request.render("pms_website_sale.pms_booking_extra_info_page", values)

    @http.route(
        ["/ebooking/booking/address"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
    )
    def booking_address(self, **kwargs):
        # todo process in _booking_address(**kwargs) -> booking_engine, errors
        errors = []
        booking_engine = request.env["pms.booking.engine"]

        try:
            if request.httprequest.method == "POST":
                self._post_booking_address(**kwargs)
                return request.redirect("/ebooking/booking/payment")
            booking_engine = self._get_booking_address()
        except ParserError as e:
            logger.debug(e)
            errors.append(e.usr_msg)
        except AvailabilityErrorGroup as e:
            return self._redirect_availability_error(e)

        countries = request.env["res.country"].sudo().search([])
        default_country = request.env.company.country_id
        # FIXME Is the booking engine really needed ?
        values = {
            "booking_engine": booking_engine,
            "countries": countries,
            "default_country_id": default_country.id,
            "partner": kwargs,
            "errors": errors,
        }
        return request.render("pms_website_sale.pms_booking_address_page", values)

    @http.route(
        ["/ebooking/booking/payment"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_payment(self):
        try:
            values = self._get_booking_payment()
        except AvailabilityErrorGroup as e:
            return self._redirect_availability_error(e)

        return request.render("pms_website_sale.pms_booking_payment_page", values)

    @http.route(
        ["/ebooking/booking/payment/transaction"],
        type="json",
        auth="public",
        method=["POST"],
    )
    def booking_payment_transaction(self, acquirer_id, **kwargs):
        try:
            tx = self._post_booking_payment_transaction(acquirer_id, **kwargs)
        except AvailabilityErrorGroup as e:
            return self._redirect_availability_error(e)

        acquirer = request.env["payment.acquirer"].browse(acquirer_id)
        return acquirer.sudo().render(tx.reference, tx.amount, tx.currency_id.id)

    @http.route(
        ["/ebooking/booking/success/<int:folio_id>/<string:access_token>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_success(self, folio_id, access_token):
        folio = request.env["pms.folio"].sudo().browse(folio_id).exists()
        if not folio:
            raise NotFound("The requested folio does not exists")
        values = self._get_booking_success(folio_id, access_token)
        return request.render("pms_website_sale.pms_booking_success_page", values)

    @http.route(
        ["/ebooking/booking/reset"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def booking_reset(self, **kwargs):
        """Reset the values in the session in order to make a new booking"""
        self._get_booking_reset()
        next_url = kwargs.get("next_url", "/ebooking/rooms")
        return request.redirect(next_url)

    def _get_booking(self):
        be_parser = BookingEngineParser(request.env, request.session)
        booking_engine = be_parser.parse()
        return booking_engine

    def _post_booking(self, **kwargs):
        be_parser = BookingEngineParser(request.env, request.session)
        if "delete" in kwargs:
            be_parser.del_room_request(kwargs.get("delete"))
        else:
            # Set daterange if it has not been set previously
            be_parser.set_daterange(
                kwargs.get("start_date"),
                kwargs.get("end_date"),
                overwrite=False,
            )
            be_parser.add_room_request(
                kwargs.get("room_type_id"),
                kwargs.get("quantity"),
                kwargs.get("start_date"),
                kwargs.get("end_date"),
            )

        be_parser.save()
        booking_engine = be_parser.parse()
        return booking_engine

    def _get_booking_extra_info(self):
        parser = BookingEngineParser(request.env, request.session)
        return parser.parse()

    def _post_booking_extra_info(self, **kwargs):
        parser = BookingEngineParser(request.env, request.session)
        parser.set_internal_comment(internal_comment=kwargs.get("notes"))
        parser.save()
        return parser.parse()

    def _get_booking_address(self):
        parser = BookingEngineParser(request.env, request.session)
        return parser.parse()

    def _post_booking_address(self, **kwargs):
        parser = BookingEngineParser(request.env, request.session)
        parser.set_partner(
            name=kwargs.get("name"),
            email=kwargs.get("email"),
            phone=kwargs.get("phone"),
            address=kwargs.get("address"),
            city=kwargs.get("city"),
            postal_code=kwargs.get("postal_code"),
            country_id=kwargs.get("country_id"),
            accepted_terms_and_conditions=kwargs.get("accepted_terms_and_conditions"),
        )
        parser.save()

    def _get_booking_payment(self):
        """
        processes the request on `/ebooking/booking/payment`
        :return: dictionary to pass onto the template renderer
        """
        errors = []
        be_parser = BookingEngineParser(request.env, request.session)
        booking_engine = be_parser.parse()

        # todo check if need to filter on other acquirer fields (currency ?)
        acquirers = request.env["payment.acquirer"].search(
            [
                ("state", "in", ["enabled", "test"]),
                ("company_id", "=", request.env.company.id),
            ]
        )
        return {
            "booking_engine": booking_engine,
            "acquirers": acquirers,
            "error_message": errors,
            "bootstrap_formatting": True,
        }

    def _post_booking_payment_transaction(self, acquirer_id, **kwargs):
        """
        Processes requests on /ebooking/booking/payment/transaction
        :param acquirer_id: the payment acquirer selected by the user
        :param kwargs:
        :return: the transaction to pass onto the acquirer renderer
        """
        acquirer = request.env["payment.acquirer"].browse(acquirer_id)
        be_parser = BookingEngineParser(request.env, request.session)
        be_parser.parse()

        if not be_parser.data.get("partner"):
            raise ValidationError(
                _("Return to the address page to fill in your details")
            )
        if not be_parser.data["partner"].get("accepted_terms_and_conditions"):
            raise ValidationError(
                _("You must accept the terms and conditions to continue.")
            )

        sudo_folio = be_parser.create_folio().sudo()
        tx = sudo_folio._create_payment_transaction(
            {
                "acquirer_id": acquirer.id,
                "type": "form",
                "return_url": f"/ebooking/booking/success"
                f"/{sudo_folio.id}/{sudo_folio.access_token}",
            }
        )
        PaymentProcessing.add_payment_transaction(tx)
        return tx

    def _get_booking_success(self, folio_id, access_token):
        """
        Processes /ebooking/booking/success for given folio id
        :return: dictionary to pass onto the template renderer
        """
        sudo_folio = request.env["pms.folio"].browse(folio_id).sudo()
        if not sudo_folio.access_token == access_token:
            raise AccessError(_("Folio token does not match"))
        sudo_folio.action_confirm()
        moves = sudo_folio._create_invoices(grouped=True, final=True)
        moves.sudo().action_post()
        request.session[BookingEngineParser.SESSION_KEY] = {}
        return {}

    def _get_booking_reset(self):
        be_parser = BookingEngineParser(request.env, request.session)
        be_parser.reset()
        be_parser.save()
        return

    def _process_availability_error(self, error: AvailabilityError):
        be_parser = BookingEngineParser(request.env, request.session)
        be_parser.del_room_request(error.room_type_id)
        be_parser.save()

    def _redirect_availability_error(self, error: AvailabilityError):
        return request.redirect("/ebooking/booking")
