from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from datetime import datetime


class PmsFolioService(Component):
    _inherit = "base.rest.service"
    _name = "pms.folio.service"
    _usage = "folios"
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
        input_param=Datamodel("pms.folio.search.param"),
        output_param=Datamodel("pms.folio.short.info", is_list=True),
        auth="public",
    )
    def get_folios(self, folio_search_param):
        domain = []
        if folio_search_param.name:
            domain.append(("name", "like", folio_search_param.name))
        if folio_search_param.id:
            domain.append(("id", "=", folio_search_param.id))
        result_folios = []
        PmsFolioShortInfo = self.env.datamodels["pms.folio.short.info"]
        for folio in (
            self.env["pms.folio"]
                .sudo()
                .search(
                domain,
            )
        ):
            reservations = []
            for reservation in folio.reservation_ids:
                reservations.append(
                    {
                        "id": reservation.id,
                        "checkin": datetime.combine(reservation.checkin, datetime.min.time()).isoformat(),
                        "checkout": datetime.combine(reservation.checkout, datetime.min.time()).isoformat(),
                        "preferredRoomId": reservation.preferred_room_id.name
                        if reservation.preferred_room_id
                        else "",
                        "roomTypeId": reservation.room_type_id.name
                        if reservation.room_type_id
                        else "",
                        "priceTotal": reservation.price_total,
                        "adults": reservation.adults,
                        "pricelist": reservation.pricelist_id.name,
                        "boardService": reservation.board_service_room_id.pms_board_service_id.name
                        if reservation.board_service_room_id
                        else "",
                    }
                )

            result_folios.append(
                PmsFolioShortInfo(
                    id=folio.id,
                    name=folio.name,
                    partnerName=folio.partner_name if folio.partner_name else "",
                    partnerPhone=folio.mobile if folio.mobile else "",
                    partnerEmail=folio.email if folio.email else "",
                    channelType=folio.channel_type_id if folio.channel_type_id else "",
                    agency=folio.agency_id if folio.agency_id else "",
                    state=dict(folio.fields_get(["state"])["state"]["selection"])[
                        folio.state
                    ],
                    pendingAmount=folio.pending_amount,
                    reservations=[] if not reservations else reservations,
                )
            )
        return result_folios

    @restapi.method(
        [
            (
                [
                    "/<int:id>/reservations",
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
                        pwaActionButtons=json.loads(reservation.pwa_action_buttons)
                        if reservation.pwa_action_buttons
                        else {},
                    )
                )
        return res
