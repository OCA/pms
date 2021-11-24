from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


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
                PmsFolioShortInfo(
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
                )
            )
        return result_folios

    @restapi.method(
        [
            (
                [
                    "/<int:id>/reservations/<int:reservation_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.reservation.short.info"),
        auth="public",
    )
    def get_reservation(self, folio_id, reservation_id):
        reservation = (
            self.env["pms.reservation"].sudo().search([("id", "=", reservation_id)])
        )
        res = []
        PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]
        if not reservation:
            pass
        else:
            services = []
            for service in reservation.service_ids:
                if service.is_board_service:
                    services.append(
                        {
                            "id": service.id,
                            "name": service.name,
                            "quantity": service.product_qty,
                            "priceTotal": service.price_total,
                            "priceSubtotal": service.price_subtotal,
                            "priceTaxes": service.price_tax,
                            "discount": service.discount,
                        }
                    )
            messages = []
            import re

            text = re.compile("<.*?>")
            for message in reservation.message_ids.sorted(key=lambda x: x.date):
                messages.append(
                    {
                        "author": message.author_id.name,
                        "date": str(message.date),
                        # print(self.env["ir.fields.converter"].text_from_html(message.body))
                        "body": re.sub(text, "", message.body),
                    }
                )
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
                priceTotal=reservation.price_room_services_set,
                priceOnlyServices=reservation.price_services
                if reservation.price_services
                else 0.0,
                priceOnlyRoom=reservation.price_total,
                pricelist=reservation.pricelist_id.name
                if reservation.pricelist_id
                else "",
                services=services if services else [],
                messages=messages,
            )
        return res

    @restapi.method(
        [
            (
                [
                    "/<int:id>/reservations/<int:reservation_id>/checkinpartners",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.checkin.partner.short.info", is_list=True),
        auth="public",
    )
    def get_checkin_partners(self, folio_id, reservation_id):
        reservation = (
            self.env["pms.reservation"].sudo().search([("id", "=", reservation_id)])
        )
        checkin_partners = []
        PmsCheckinPartnerShortInfo = self.env.datamodels[
            "pms.checkin.partner.short.info"
        ]
        if not reservation:
            pass
        else:
            for checkin_partner in reservation.checkin_partner_ids:
                checkin_partners.append(
                    PmsCheckinPartnerShortInfo(
                        id=checkin_partner.id,
                        reservationId=checkin_partner.reservation_id.id,
                        name=checkin_partner.name if checkin_partner.name else "",
                        email=checkin_partner.email if checkin_partner.email else "",
                        mobile=checkin_partner.mobile if checkin_partner.mobile else "",
                        nationality=checkin_partner.nationality_id.name
                        if checkin_partner.nationality_id
                        else "",
                        documentType=checkin_partner.document_type.name
                        if checkin_partner.document_type
                        else "",
                        documentNumber=checkin_partner.document_number
                        if checkin_partner.document_number
                        else "",
                        gender=checkin_partner.gender if checkin_partner.gender else "",
                        state=dict(
                            checkin_partner.fields_get(["state"])["state"]["selection"]
                        )[checkin_partner.state],
                    )
                )
        return checkin_partners
