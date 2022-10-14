from datetime import datetime, timedelta

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsReservationService(Component):
    _inherit = "base.rest.service"
    _name = "pms.reservation.service"
    _usage = "reservations"
    _collection = "pms.services"

    # ------------------------------------------------------------------------------------
    # HEAD RESERVATION--------------------------------------------------------------------
    # ------------------------------------------------------------------------------------

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.search.param", is_list=False),
        output_param=Datamodel("pms.reservation.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_reservation(self, reservation_id, pms_search_param):
        domain = list()
        domain.append(("id", "=", reservation_id))
        if pms_search_param.pmsPropertyId:
            domain.append(("pms_property_id", "=", pms_search_param.pmsPropertyId))
        reservation = self.env["pms.reservation"].search(domain)
        res = []
        PmsReservationInfo = self.env.datamodels["pms.reservation.info"]
        if not reservation:
            pass
        else:
            # messages = []
            # import re

            # text = re.compile("<.*?>")
            # for message in reservation.message_ids.sorted(key=lambda x: x.date):
            #     messages.append(
            #         {
            #             "author": message.author_id.name,
            #             "date": str(message.date),
            #             # print(self.env["ir.fields.converter"].text_from_html(message.body))
            #             "body": re.sub(text, "", message.body),
            #         }
            #     )
            res = PmsReservationInfo(
                id=reservation.id,
                name=reservation.name,
                folioId=reservation.folio_id.id,
                folioSequence=reservation.folio_sequence,
                partnerName=reservation.partner_name,
                boardServiceId=reservation.board_service_room_id.id
                if reservation.board_service_room_id
                else None,
                saleChannelId=reservation.sale_channel_origin_id.id
                if reservation.sale_channel_origin_id
                else None,
                agencyId=reservation.agency_id.id if reservation.agency_id else None,
                userId=reservation.user_id.id if reservation.user_id else None,
                checkin=datetime.combine(
                    reservation.checkin, datetime.min.time()
                ).isoformat(),
                checkout=datetime.combine(
                    reservation.checkout, datetime.min.time()
                ).isoformat(),
                arrivalHour=reservation.arrival_hour,
                departureHour=reservation.departure_hour,
                roomTypeId=reservation.room_type_id.id
                if reservation.room_type_id
                else None,
                preferredRoomId=reservation.preferred_room_id.id
                if reservation.preferred_room_id
                else None,
                pricelistId=reservation.pricelist_id.id
                if reservation.pricelist_id
                else None,
                adults=reservation.adults if reservation.adults else None,
                overbooking=reservation.overbooking,
                externalReference=reservation.external_reference
                if reservation.external_reference
                else None,
                stateCode=reservation.state,
                stateDescription=dict(
                    reservation.fields_get(["state"])["state"]["selection"]
                )[reservation.state],
                children=reservation.children if reservation.children else None,
                readyForCheckin=reservation.ready_for_checkin,
                allowedCheckout=reservation.allowed_checkout,
                isSplitted=reservation.splitted,
                pendingCheckinData=reservation.pending_checkin_data,
                createDate=reservation.create_date.isoformat(),
                segmentationId=reservation.segmentation_ids[0].id
                if reservation.segmentation_ids
                else None,
                toAssign=reservation.to_assign,
                reservationType=reservation.reservation_type,
                priceTotal=round(reservation.price_room_services_set, 2),
                discount=round(reservation.discount, 2),
                commissionAmount=round(reservation.commission_amount, 2)
                if reservation.commission_amount
                else None,
                priceOnlyServices=round(reservation.price_services, 2),
                priceOnlyRoom=round(reservation.price_total, 2),
            )
        return res

    @restapi.method(
        [
            (
                [
                    "/p/<int:reservation_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.reservation.info", is_list=False),
        auth="jwt_api_pms",
    )
    # TODO: route changed because bug route CORS patch
    def update_reservation(self, reservation_id, reservation_data):
        reservation = self.env["pms.reservation"].search([("id", "=", reservation_id)])
        reservation_vals = {}
        if reservation_data.reservationLines:
            reservation_lines_vals = []
            date_list = []
            for line_data in sorted(
                reservation_data.reservationLines,
                key=lambda x: datetime.strptime(x.date, "%Y-%m-%d"),
            ):
                date_line = datetime.strptime(line_data.date, "%Y-%m-%d").date()
                date_list.append(date_line)
                # 1- update values in existing lines
                reservation_line = self.env["pms.reservation.line"].search(
                    [("reservation_id", "=", reservation_id), ("date", "=", date_line)]
                )
                if reservation_line:
                    line_vals = self._get_reservation_lines_mapped(
                        line_data, reservation_line
                    )
                    if line_vals:
                        reservation_lines_vals.append(
                            (1, reservation_line.id, line_vals)
                        )
                # 2- create new lines
                else:
                    line_vals = self._get_reservation_lines_mapped(line_data)
                    line_vals["date"] = line_data.date
                    reservation_lines_vals.append((0, False, line_vals))
            # 3- delete old lines:
            for line in reservation.reservation_line_ids.filtered(
                lambda l: l.date not in date_list
            ):
                reservation_lines_vals.append((2, line.id))
            if reservation_lines_vals:
                reservation_vals.update(
                    {
                        "reservation_line_ids": reservation_lines_vals,
                    }
                )

        if reservation_data.preferredRoomId:
            reservation_vals.update(
                {"preferred_room_id": reservation_data.preferredRoomId}
            )
        if reservation_data.boardServiceId:
            reservation_vals.update(
                {"board_service_room_id": reservation_data.boardServiceId}
            )
        if reservation_data.pricelistId:
            reservation_vals.update({"pricelist_id": reservation_data.pricelistId})
        if reservation_data.adults:
            reservation_vals.update({"adults": reservation_data.adults})
        if reservation_data.children:
            reservation_vals.update({"children": reservation_data.children})
        if reservation_data.segmentationId:
            reservation_vals.update(
                {"segmentation_ids": [(6, 0, [reservation_data.segmentationId])]}
            )
        if reservation_data.toAssign is not None and not reservation_data.toAssign:
            reservation.action_assign()
        if reservation_data.stateCode == "cancel":
            reservation.action_cancel()
        if reservation_data.stateCode == "confirm":
            reservation.confirm()
        if reservation_vals:
            reservation.write(reservation_vals)

    def _get_reservation_lines_mapped(self, origin_data, reservation_line=False):
        # Return dict witch reservation.lines values (only modified if line exist,
        # or all pass values if line not exist)
        line_vals = {}
        if origin_data.price and (
            not reservation_line or origin_data.price != reservation_line.price
        ):
            line_vals["price"] = origin_data.price
        if origin_data.discount and (
            not reservation_line or origin_data.discount != reservation_line.discount
        ):
            line_vals["discount"] = origin_data.discount
        if origin_data.cancelDiscount and (
            not reservation_line
            or origin_data.cancelDiscount != reservation_line.cancelDiscount
        ):
            line_vals["cancel_discount"] = origin_data.cancelDiscount
        if origin_data.roomId and (
            not reservation_line or origin_data.roomId != reservation_line.room_id
        ):
            line_vals["room_id"] = origin_data.roomId
        return line_vals

    # ------------------------------------------------------------------------------------
    # RESERVATION LINES-------------------------------------------------------------------
    # ------------------------------------------------------------------------------------

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/reservation-lines",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.reservation.line.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservation_line(self, reservation_id):
        reservation = self.env["pms.reservation"].search([("id", "=", reservation_id)])
        if not reservation:
            raise MissingError(_("Reservation not found"))
        result_lines = []
        PmsReservationLineInfo = self.env.datamodels["pms.reservation.line.info"]
        for reservation_line in reservation.reservation_line_ids:
            result_lines.append(
                PmsReservationLineInfo(
                    id=reservation_line.id,
                    date=datetime.combine(
                        reservation_line.date, datetime.min.time()
                    ).isoformat(),
                    price=round(reservation_line.price, 2),
                    discount=round(reservation_line.discount, 2),
                    cancelDiscount=round(reservation_line.cancel_discount, 2),
                    roomId=reservation_line.room_id.id,
                    reservationId=reservation_line.reservation_id.id,
                    pmsPropertyId=reservation_line.pms_property_id.id,
                )
            )
        return result_lines

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/reservation-lines",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.reservation.line.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_reservation_line(self, reservation_id, reservation_line_info):
        reservation = self.env["pms.reservation"].search([("id", "=", reservation_id)])
        date = datetime.strptime(reservation_line_info.date, "%Y-%m-%d").date()
        if not reservation:
            raise MissingError(_("Reservation not found"))
        if not reservation_line_info.date or not reservation_line_info.price:
            raise MissingError(_("Date and price are required"))
        if (
            date != reservation.checkin - timedelta(days=1)
            and date != reservation.checkout
        ):
            raise MissingError(
                _("It is only allowed to create contiguous nights to the reservation")
            )
        vals = dict()
        vals.update(
            {
                "reservation_id": reservation.id,
                "date": date,
                "price": reservation_line_info.price,
                "room_id": reservation_line_info.roomId
                if reservation_line_info.roomId
                else reservation.preferred_room_id.id,
            }
        )
        self.env["pms.reservation.line"].create(vals)

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/reservation-lines/<int:reservation_line_id>",
                ],
                "DELETE",
            )
        ],
        auth="jwt_api_pms",
    )
    def delete_reservation_line(self, reservation_id, reservation_line_id):
        reservation = self.env["pms.reservation"].search([("id", "=", reservation_id)])
        line = reservation.reservation_line_ids.filtered(
            lambda l: l.id == reservation_line_id
        )
        if line and (
            line.date == min(reservation.reservation_line_ids.mapped("date"))
            or line.date == max(reservation.reservation_line_ids.mapped("date"))
        ):
            line.unlink()
        else:
            raise MissingError(_("It was not possible to remove the reservation line"))

    @restapi.method(
        [
            (
                [
                    "/p/<int:_reservation_id>/reservation-lines/<int:reservation_line_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.reservation.line.info", is_list=False),
        auth="jwt_api_pms",
    )
    def update_reservation_lines(
        self, _reservation_id, reservation_line_id, reservation_line_param
    ):
        if reservation_line_param.roomId:
            reservation_line_id = self.env["pms.reservation.line"].browse(
                reservation_line_id
            )
            reservation_line_id.room_id = reservation_line_param.roomId

    # ------------------------------------------------------------------------------------
    # RESERVATION SERVICES----------------------------------------------------------------
    # ------------------------------------------------------------------------------------

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/services",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.service.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservation_services(self, reservation_id):
        reservation = self.env["pms.reservation"].search([("id", "=", reservation_id)])
        if not reservation:
            raise MissingError(_("Reservation not found"))

        result_services = []
        PmsServiceInfo = self.env.datamodels["pms.service.info"]
        for service in reservation.service_ids:
            PmsServiceLineInfo = self.env.datamodels["pms.service.line.info"]
            service_lines = []
            for line in service.service_line_ids:
                service_lines.append(
                    PmsServiceLineInfo(
                        id=line.id,
                        date=datetime.combine(
                            line.date, datetime.min.time()
                        ).isoformat(),
                        priceUnit=line.price_unit,
                        discount=line.discount,
                        quantity=line.day_qty,
                    )
                )

            result_services.append(
                PmsServiceInfo(
                    id=service.id,
                    name=service.name,
                    productId=service.product_id.id,
                    quantity=service.product_qty,
                    priceTotal=round(service.price_total, 2),
                    priceSubtotal=round(service.price_subtotal, 2),
                    priceTaxes=round(service.price_tax, 2),
                    discount=round(service.discount, 2),
                    isBoardService=service.is_board_service,
                    serviceLines=service_lines,
                )
            )
        return result_services

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/services",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.service.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_reservation_service(self, reservation_id, service_info):
        reservation = self.env["pms.reservation"].search([("id", "=", reservation_id)])
        if not reservation:
            raise MissingError(_("Reservation not found"))
        vals = {
            "product_id": service_info.productId,
            "reservation_id": reservation.id,
            "is_board_service": service_info.isBoardService or False,
        }
        if service_info.serviceLines:
            vals["service_line_ids"] = [
                (
                    0,
                    False,
                    {
                        "date": line.date,
                        "price_unit": line.priceUnit,
                        "discount": line.discount or 0,
                        "day_qty": line.quantity,
                    },
                )
                for line in service_info.serviceLines
            ]
        service = self.env["pms.service"].create(vals)
        return service.id

    # ------------------------------------------------------------------------------------
    # RESERVATION CHECKINS----------------------------------------------------------------
    # ------------------------------------------------------------------------------------

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/checkin-partners",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.checkin.partner.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_checkin_partners(self, reservation_id):
        reservation = self.env["pms.reservation"].browse(reservation_id)
        checkin_partners = []
        PmsCheckinPartnerInfo = self.env.datamodels["pms.checkin.partner.info"]
        if not reservation:
            pass
        else:
            # TODO Review state draft
            for checkin_partner in reservation.checkin_partner_ids.filtered(
                lambda ch: ch.state != "dummy"
            ):
                if checkin_partner.document_expedition_date:
                    document_expedition_date = (
                        checkin_partner.document_expedition_date.strftime("%d/%m/%Y")
                    )
                if checkin_partner.birthdate_date:
                    birthdate_date = checkin_partner.birthdate_date.strftime("%d/%m/%Y")
                checkin_partners.append(
                    PmsCheckinPartnerInfo(
                        id=checkin_partner.id,
                        reservationId=checkin_partner.reservation_id.id,
                        name=checkin_partner.name if checkin_partner.name else "",
                        firstname=checkin_partner.firstname
                        if checkin_partner.firstname
                        else None,
                        lastname=checkin_partner.lastname
                        if checkin_partner.lastname
                        else None,
                        lastname2=checkin_partner.lastname2
                        if checkin_partner.lastname2
                        else None,
                        email=checkin_partner.email if checkin_partner.email else "",
                        mobile=checkin_partner.mobile if checkin_partner.mobile else "",
                        documentType=checkin_partner.document_type.id
                        if checkin_partner.document_type
                        else None,
                        documentNumber=checkin_partner.document_number
                        if checkin_partner.document_number
                        else None,
                        documentExpeditionDate=document_expedition_date
                        if checkin_partner.document_expedition_date
                        else None,
                        documentSupportNumber=checkin_partner.support_number
                        if checkin_partner.support_number
                        else None,
                        gender=checkin_partner.gender if checkin_partner.gender else "",
                        birthdate=birthdate_date
                        if checkin_partner.birthdate_date
                        else None,
                        residenceStreet=checkin_partner.residence_street
                        if checkin_partner.residence_street
                        else None,
                        zip=checkin_partner.residence_zip
                        if checkin_partner.residence_zip
                        else None,
                        residenceCity=checkin_partner.residence_city
                        if checkin_partner.residence_city
                        else None,
                        nationality=checkin_partner.residence_country_id.id
                        if checkin_partner.residence_country_id
                        else None,
                        countryState=checkin_partner.residence_state_id.id
                        if checkin_partner.residence_state_id
                        else None,
                        countryId=checkin_partner.residence_country_id.id
                        if checkin_partner.residence_country_id
                        else None,
                        checkinPartnerState=checkin_partner.state,
                    )
                )
        return checkin_partners

    @restapi.method(
        [
            (
                [
                    "/p/<int:reservation_id>/checkin-partners/<int:checkin_partner_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.checkin.partner.info", is_list=False),
        auth="jwt_api_pms",
    )
    def write_reservation_checkin_partner(
        self, reservation_id, checkin_partner_id, pms_checkin_partner_info
    ):
        checkin_partner = self.env["pms.checkin.partner"].search(
            [("id", "=", checkin_partner_id), ("reservation_id", "=", reservation_id)]
        )
        if checkin_partner:
            checkin_partner.write(
                self.mapping_checkin_partner_values(pms_checkin_partner_info)
            )

    @restapi.method(
        [
            (
                [
                    "/partner-as-host",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.partner.search.param", is_list=False),
        output_param=Datamodel("pms.reservation.short.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservations_for_partners_as_host(self, pms_partner_search_param):
        checkins = self.env["pms.checkin.partner"].search(
            [("partner_id", "=", pms_partner_search_param.id)]
        )
        PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]
        reservations = []
        if checkins:
            for checkin in checkins:
                reservation = self.env["pms.reservation"].search(
                    [("id", "=", checkin.reservation_id.id)]
                )

                reservations.append(
                    PmsReservationShortInfo(
                        id=reservation.id,
                        checkin=reservation.checkin.strftime("%d/%m/%Y"),
                        checkout=reservation.checkout.strftime("%d/%m/%Y"),
                        adults=reservation.adults,
                        priceTotal=round(reservation.price_room_services_set, 2),
                        stateCode=reservation.state,
                        paymentState=reservation.folio_payment_state,
                    )
                )
        return reservations

    @restapi.method(
        [
            (
                [
                    "/partner-as-customer",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.partner.search.param", is_list=False),
        output_param=Datamodel("pms.reservation.short.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservations_for_partner_as_customer(self, pms_partner_search_param):
        partnerReservations = self.env["pms.reservation"].search(
            [("partner_id", "=", pms_partner_search_param.id)]
        )
        PmsReservationShortInfo = self.env.datamodels["pms.reservation.short.info"]
        reservations = []
        for reservation in partnerReservations:
            reservations.append(
                PmsReservationShortInfo(
                    checkin=reservation.checkin.strftime("%d/%m/%Y"),
                    checkout=reservation.checkout.strftime("%d/%m/%Y"),
                    adults=reservation.adults,
                    priceTotal=round(reservation.price_room_services_set, 2),
                    stateCode=reservation.state,
                    paymentState=reservation.folio_payment_state,
                )
            )
        return reservations

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/checkin-partners",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.checkin.partner.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_reservation_checkin_partner(
        self, reservation_id, pms_checkin_partner_info
    ):
        reservation_rec = self.env["pms.reservation"].browse(reservation_id)
        if any(
            reservation_rec.checkin_partner_ids.filtered(lambda ch: ch.state == "dummy")
        ):
            checkin_partner_last_id = max(
                reservation_rec.checkin_partner_ids.filtered(
                    lambda ch: ch.state == "dummy"
                )
            ).id
            checkin_partner = self.env["pms.checkin.partner"].browse(
                checkin_partner_last_id
            )
            checkin_partner.write(
                self.mapping_checkin_partner_values(pms_checkin_partner_info)
            )

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/checkin-partners/<int:checkin_partner_id>",
                ],
                "DELETE",
            )
        ],
        auth="jwt_api_pms",
    )
    def delete_reservation_checkin_partner(self, reservation_id, checkin_partner_id):
        reservation = self.env["pms.reservation"].browse(reservation_id)
        reservation.adults = reservation.adults - 1

    def mapping_checkin_partner_values(self, pms_checkin_partner_info):
        vals = dict()
        checkin_partner_fields = {
            "firstname": pms_checkin_partner_info.firstname,
            "lastname": pms_checkin_partner_info.lastname,
            "lastname2": pms_checkin_partner_info.lastname2,
            "email": pms_checkin_partner_info.email,
            "mobile": pms_checkin_partner_info.mobile,
            "document_type": pms_checkin_partner_info.documentType,
            "document_number": pms_checkin_partner_info.documentNumber,
            "support_number": pms_checkin_partner_info.documentSupportNumber,
            "gender": pms_checkin_partner_info.gender,
            "residence_street": pms_checkin_partner_info.residenceStreet,
            "nationality_id": pms_checkin_partner_info.nationality,
            "residence_zip": pms_checkin_partner_info.zip,
            "residence_city": pms_checkin_partner_info.residenceCity,
            "residence_state_id": pms_checkin_partner_info.countryState,
            "residence_country_id": pms_checkin_partner_info.countryId,
        }
        if pms_checkin_partner_info.documentExpeditionDate:
            document_expedition_date = datetime.strptime(
                pms_checkin_partner_info.documentExpeditionDate, "%d/%m/%Y"
            )
            document_expedition_date = document_expedition_date.strftime("%Y-%m-%d")
            vals.update({"document_expedition_date": document_expedition_date})
        if pms_checkin_partner_info.birthdate:
            birthdate = datetime.strptime(
                pms_checkin_partner_info.birthdate, "%d/%m/%Y"
            )
            birthdate = birthdate.strftime("%Y-%m-%d")
            vals.update({"birthdate_date": birthdate})
        for k, v in checkin_partner_fields.items():
            if v:
                vals.update({k: v})
        return vals
