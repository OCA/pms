from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsFolioService(Component):
    _inherit = "base.rest.service"
    _name = "pms.folio.service"
    _usage = "folios"
    _collection = "pms.services"

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
        output_param=Datamodel("pms.folio.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folios(self, folio_search_param):
        domain = list()
        domain.append(("checkin", ">=", folio_search_param.date_from))
        domain.append(("checkout", "<", folio_search_param.date_to))
        domain.append(("pms_property_id", "=", folio_search_param.pms_property_id))
        result_folios = []

        reservations_result = (
            self.env["pms.reservation"].search(domain).mapped("folio_id").ids
        )

        PmsFolioInfo = self.env.datamodels["pms.folio.info"]
        for folio in self.env["pms.folio"].search(
            [("id", "in", reservations_result)],
        ):
            reservations = []
            for reservation in folio.reservation_ids:
                reservation_lines = []
                for reservation_line in reservation.reservation_line_ids:
                    reservation_lines.append(
                        {
                            "id": reservation_line.id,
                            "date": reservation_line.date,
                            "roomId": reservation_line.room_id.id,
                        }
                    )

                reservations.append(
                    {
                        "id": reservation.id,
                        "checkin": datetime.combine(
                            reservation.checkin, datetime.min.time()
                        ).isoformat(),
                        "checkout": datetime.combine(
                            reservation.checkout, datetime.min.time()
                        ).isoformat(),
                        "preferredRoomId": reservation.preferred_room_id.name
                        if reservation.preferred_room_id
                        else "",
                        "roomTypeId": reservation.room_type_id.name
                        if reservation.room_type_id
                        else "",
                        "priceTotal": reservation.price_total,
                        "adults": reservation.adults,
                        "pricelist": reservation.pricelist_id.name,
                        "boardService": (
                            reservation.board_service_room_id.pms_board_service_id.name
                        )
                        if reservation.board_service_room_id
                        else "",
                        "reservationLines": []
                        if not reservation_lines
                        else reservation_lines,
                        "folioId": reservation.folio_id.id
                        if reservation.folio_id
                        else "",
                    }
                )
            result_folios.append(
                PmsFolioInfo(
                    id=folio.id,
                    name=folio.name,
                    partnerName=folio.partner_name if folio.partner_name else "",
                    partnerPhone=folio.mobile if folio.mobile else "",
                    partnerEmail=folio.email if folio.email else "",
                    saleChannel=folio.channel_type_id.name
                    if folio.channel_type_id
                    else "",
                    agency=folio.agency_id.name if folio.agency_id else "",
                    state=dict(folio.fields_get(["state"])["state"]["selection"])[
                        folio.state
                    ],
                    pendingAmount=folio.pending_amount,
                    reservations=[] if not reservations else reservations,
                    salesPerson=folio.user_id.name if folio.user_id else "",
                    paymentState=dict(
                        folio.fields_get(["payment_state"])["payment_state"][
                            "selection"
                        ]
                    )[folio.payment_state]
                    if folio.payment_state
                    else "",
                    propertyId=folio.pms_property_id,
                )
            )
        return result_folios

    @restapi.method(
        [
            (
                [
                    "/<int:id>/payments",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.search.param"),
        output_param=Datamodel("pms.payment.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_folio_payments(self, folio_id, pms_search_param):
        domain = list()
        domain.append(("id", "=", folio_id))
        domain.append(("pms_property_id", "=", pms_search_param.pms_property_id))
        folio = self.env["pms.folio"].search(domain)
        payments = []
        PmsPaymentInfo = self.env.datamodels["pms.payment.info"]
        if not folio:
            pass
        else:
            if folio.payment_state == "not_paid":
                pass
                # si el folio está sin pagar no tendrá ningún pago o envíar []?
            else:
                if folio.statement_line_ids:
                    for payment in folio.statement_line_ids:
                        payments.append(
                            PmsPaymentInfo(
                                id=payment.id,
                                amount=payment.amount,
                                journalId=payment.journal_id,
                                journalName=payment.journal_id.name,
                                date=str(payment.date),
                            )
                        )
                if folio.payment_ids:
                    if folio.payment_ids:
                        for payment in folio.payment_ids:
                            payments.append(
                                PmsPaymentInfo(
                                    id=payment.id,
                                    amount=payment.amount,
                                    journalId=payment.journal_id,
                                    journalName=payment.journal_id.name,
                                    date=str(payment.date),
                                )
                            )
        return payments

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.reservation.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_reservation(self, pms_reservation_info):
        reservation = self.env["pms.reservation"].create(
            {
                "partner_name": pms_reservation_info.partner,
                "pms_property_id": pms_reservation_info.pms_property_id,
                "room_type_id": pms_reservation_info.roomTypeId,
                "pricelist_id": pms_reservation_info.pricelistId,
                "checkin": pms_reservation_info.checkin,
                "checkout": pms_reservation_info.checkout,
                "board_service_room_id": pms_reservation_info.boardServiceId,
                "channel_type_id": pms_reservation_info.channelTypeId,
            }
        )
        return reservation.id
