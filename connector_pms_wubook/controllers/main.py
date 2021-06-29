# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from werkzeug import urls

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

WUBOOK_PUSH_BASE_URLS = {
    "reservations": "/wubook/push/reservations",
    "rooms": "/wubook/push/rooms",
}


class WubookPushURL(http.Controller):
    # Called when created a reservation in wubook
    @http.route(
        urls.url_join(WUBOOK_PUSH_BASE_URLS["reservations"], "<string:security_token>"),
        type="http",
        cors="*",
        auth="public",
        methods=["POST"],
        # website=True,
        csrf=False,
    )
    def wubook_push_reservations(self, security_token, **kwargs):
        reservation_code = kwargs.get("rcode")
        property_code = kwargs.get("lcode")

        # Correct Input?
        if not property_code or not reservation_code or not security_token:
            raise ValidationError(_("Invalid Input Parameters!"))

        # WuBook Check
        if reservation_code == "2000" and property_code == "1000":
            return request.make_response("200 OK", [("Content-Type", "text/plain")])

        user = request.env.ref("base.user_root")

        # Get Backend
        backend = (
            request.env["channel.wubook.backend"]
            .with_user(user)
            .search(
                [
                    ("security_token", "=", security_token),
                    ("property_code", "=", property_code),
                ]
            )
        )
        if not backend:
            raise ValidationError(_("Can't found a backend!"))

        if backend.user_id:
            user = backend.user_id
            backend = backend.with_user(user)

        request.env["channel.wubook.pms.folio"].with_user(
            user
        ).with_delay().import_record(backend, reservation_code)

        return request.make_response("200 OK", [("Content-Type", "text/plain")])

    # TODO: finish this
    # # Called when modify room values
    # @http.route(
    #     urls.url_join(WUBOOK_PUSH_BASE_URLS['rooms'], '<string:security_token>'),
    #     type="http",
    #     cors="*",
    #     auth="public",
    #     methods=["POST"],
    #     website=True,
    #     csrf=False,
    # )
    # def wubook_push_rooms(self, security_token, **kwargs):
    #     lcode = kwargs.get("lcode")
    #     dfrom = kwargs.get("dfrom")
    #     dto = kwargs.get("dto")
    #
    #     # Correct Input?
    #     if not lcode or not dfrom or not dto:
    #         raise ValidationError(_("Invalid Input Parameters!"))
    #
    #     # Get Backend
    #     backend = request.env["channel.backend"].search(
    #         [
    #             ("security_token", "=", security_token),
    #             ("lcode", "=", lcode),
    #         ]
    #     )
    #     if not backend:
    #         raise ValidationError(_("Can't found a backend!"))
    #
    #     odoo_dfrom = datetime.strptime(dfrom, DEFAULT_WUBOOK_DATE_FORMAT).strftime(
    #         DEFAULT_SERVER_DATE_FORMAT
    #     )
    #     odoo_dto = datetime.strptime(dto, DEFAULT_WUBOOK_DATE_FORMAT).strftime(
    #         DEFAULT_SERVER_DATE_FORMAT
    #     )
    #
    #     request.env["channel.hotel.room.type.availability"].import_availability(
    #         backend, odoo_dfrom, odoo_dto
    #     )
    #     request.env[
    #         "channel.hotel.room.type.restriction.item"
    #     ].import_restriction_values(backend, odoo_dfrom, odoo_dto, False)
    #     request.env["channel.product.pricelist.item"].import_pricelist_values(
    #         backend, odoo_dfrom, odoo_dto, False
    #     )
    #
    #     return request.make_response("200 OK", [("Content-Type", "text/plain")])
