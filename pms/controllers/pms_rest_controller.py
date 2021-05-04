import datetime

from odoo import _, http
from odoo.http import request

from odoo.tools.misc import formatLang, format_date, get_lang


class PmsReservationRestController(http.Controller):
    @http.route(
        "/reservations",
        type="json",
        website=True,
        auth="public",
    )
    def room_type_list(self):
        payload = http.request.jsonrequest.get("params")

        return self._get_available_room_types(payload)

    def _get_available_room_types(self, payload):
        room_types = []
        checkin = payload["checkin"]
        checkin = datetime.datetime.strptime(checkin, get_lang(request.env).date_format).date()

        checkout = payload["checkout"]
        checkout = datetime.datetime.strptime(checkout, get_lang(request.env).date_format).date()

        pms_property_id = int(payload["pms_property_id"])
        pricelist_id = int(payload["pricelist_id"])

        reservation = False
        if isinstance(payload["reservation_id"], int):
            reservation_id = int(payload["reservation_id"])

            reservation = (
                request.env["pms.reservation"]
                .sudo()
                .search([("id", "=", int(reservation_id))])
            )
        if not reservation:
            reservation_line_ids = False
        else:
            reservation_line_ids = reservation.reservation_line_ids.ids

        rooms_avail = (
            request.env["pms.availability.plan"]
            .sudo()
            .rooms_available(
                checkin=checkin,
                checkout=checkout,
                current_lines=reservation_line_ids,
                pricelist_id=pricelist_id,
                pms_property_id=pms_property_id,
            )
        )

        pms_room_types = request.env["pms.room.type"].sudo().search([])

        for room_type in pms_room_types.filtered(lambda r: r.total_rooms_count > 0):
            count = len(
                rooms_avail.filtered(lambda r: r.room_type_id.id == room_type.id)
            )
            room_types.append(
                {
                    "id": room_type.id,
                    "name": room_type.name + " (" + str(count) + ")",
                }
            )

        return room_types

    #
    # @http.route(
    #     "/reservation/<int:reservation_id>",
    #     type="http",
    #     auth="user",
    #     methods=["GET", "POST"],
    #     website=True,
    # )
    # def reservation_detail(self, reservation_id, **post):
    #     reservation = request.env["pms.reservation"].browse([reservation_id])
    #     if not reservation:
    #         raise MissingError(_("This document does not exist."))
    #     values = {
    #         "page_name": "Reservation",
    #         "reservation": reservation,
    #     }
    #     if post and "message" in post:
    #         try:
    #             reservation.message_post(
    #                 subject=_("PWA Message"),
    #                 body=post["message"],
    #                 message_type="comment",
    #             )
    #         except Exception as e:
    #             _logger.critical(e)
    #     return http.request.render("pms_pwa.roomdoo_reservation_detail", values)
