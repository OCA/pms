import json

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsReservationService(Component):
    _inherit = "base.rest.service"
    _name = "pms.reservation.service"
    _usage = "reservations"
    _collection = "pms.reservation.service"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.reservation.search.param"),
        output_param=Datamodel("pms.reservation.short.info", is_list=True),
        auth="public",
    )
    def search(self, reservation_search_param):
        domain = []
        if reservation_search_param.name:
            domain.append(("name", "like", reservation_search_param.name))
        if reservation_search_param.id:
            domain.append(("id", "=", reservation_search_param.id))
        res = []
        PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]
        for reservation in (
            self.env["pms.reservation"]
            .sudo()
            .search(
                domain,
            )
        ):
            res.append(
                PmsReservationShortInfo(
                    id=reservation.id,
                    partner=reservation.partner_id.name,
                    checkin=str(reservation.checkin),
                    checkout=str(reservation.checkout),
                    preferredRoomId=reservation.preferred_room_id.name
                    if reservation.preferred_room_id
                    else "",
                    roomTypeId=reservation.room_type_id.name
                    if reservation.room_type_id
                    else "",
                    name=reservation.name,
                    partnerRequests=reservation.partner_requests
                    if reservation.partner_requests
                    else "",
                    state=dict(reservation.fields_get(["state"])["state"]["selection"])[
                        reservation.state
                    ],
                    priceTotal=reservation.price_total,
                    adults=reservation.adults,
                    channelTypeId=reservation.channel_type_id
                    if reservation.channel_type_id
                    else "",
                    agencyId=reservation.agency_id if reservation.agency_id else "",
                    boardServiceId=reservation.board_service_room_id.pms_board_service_id.name
                    if reservation.board_service_room_id
                    else "",
                    checkinsRatio=reservation.checkins_ratio,
                    outstanding=reservation.folio_id.pending_amount,
                    pricelist=reservation.pricelist_id.name,
                    folioId=reservation.folio_id.id,
                    pwaActionButtons=json.loads(reservation.pwa_action_buttons)
                    if reservation.pwa_action_buttons
                    else {},
                )
            )
        return res

    @restapi.method(
        [
            (
                [
                    "/<int:id>/cancellation",
                ],
                "POST",
            )
        ],
        auth="public",
    )
    def cancel_reservation(self, reservation_id):
        reservation = (
            self.env["pms.reservation"].sudo().search([("id", "=", reservation_id)])
        )
        if not reservation:
            pass
        else:
            reservation.sudo().action_cancel()

    @restapi.method(
        [
            (
                [
                    "/<int:id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.reservation.short.info"),
        auth="public",
    )
    def get_reservation(self, reservation_id):
        reservation = (
            self.env["pms.reservation"].sudo().search([("id", "=", reservation_id)])
        )
        res = False
        if not reservation:
            pass
        else:
            PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]
            res = PmsReservationShortInfo(
                id=reservation.id,
                partner=reservation.partner_id.name,
                checkin=str(reservation.checkin),
                checkout=str(reservation.checkout),
                preferredRoomId=reservation.preferred_room_id.name
                if reservation.preferred_room_id
                else "",
                roomTypeId=reservation.room_type_id.name
                if reservation.room_type_id
                else "",
                name=reservation.name,
                partnerRequests=reservation.partner_requests
                if reservation.partner_requests
                else "",
                state=dict(reservation.fields_get(["state"])["state"]["selection"])[
                    reservation.state
                ],
                priceTotal=reservation.price_total,
                adults=reservation.adults,
                channelTypeId=reservation.channel_type_id
                if reservation.channel_type_id
                else "",
                agencyId=reservation.agency_id if reservation.agency_id else "",
                boardServiceId=reservation.board_service_room_id.pms_board_service_id.name
                if reservation.board_service_room_id
                else "",
                checkinsRatio=reservation.checkins_ratio,
                outstanding=reservation.folio_id.pending_amount,
                pricelist=reservation.pricelist_id.name,
                folioId=reservation.folio_id.id,
                pwaActionButtons={},
            )
        return res

    @restapi.method(
        [
            (
                [
                    "/folio/<int:id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.reservation.short.info", is_list=True),
        auth="public",
    )
    def get_reservations(self, folio_id):
        folio = (
            self.env["pms.folio"].sudo().search([("id", "=", folio_id)])
        )
        res = []
        if not folio.reservation_ids:
            pass
        else:
            PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]

            for reservation in folio.reservation_ids:
                res.append(
                    PmsReservationShortInfo(
                        id=reservation.id,
                        partner=reservation.partner_id.name,
                        checkin=str(reservation.checkin),
                        checkout=str(reservation.checkout),
                        preferredRoomId=reservation.preferred_room_id.name
                        if reservation.preferred_room_id
                        else "",
                        roomTypeId=reservation.room_type_id.name
                        if reservation.room_type_id
                        else "",
                        name=reservation.name,
                        partnerRequests=reservation.partner_requests
                        if reservation.partner_requests
                        else "",
                        state=dict(reservation.fields_get(["state"])["state"]["selection"])[
                            reservation.state
                        ],
                        priceTotal=reservation.price_total,
                        adults=reservation.adults,
                        channelTypeId=reservation.channel_type_id
                        if reservation.channel_type_id
                        else "",
                        agencyId=reservation.agency_id if reservation.agency_id else "",
                        boardServiceId=reservation.board_service_room_id.pms_board_service_id.name
                        if reservation.board_service_room_id
                        else "",
                        checkinsRatio=reservation.checkins_ratio,
                        outstanding=reservation.folio_id.pending_amount,
                        pricelist=reservation.pricelist_id.name,
                        folioId=reservation.folio_id.id,
                        pwaActionButtons=json.loads(reservation.pwa_action_buttons)
                        if reservation.pwa_action_buttons
                        else {},
                    )
                )
        return res
