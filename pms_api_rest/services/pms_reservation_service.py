import base64
import os
import re
import tempfile
from datetime import datetime, timedelta

from odoo import _, fields
from odoo.exceptions import AccessError, MissingError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from odoo.addons.pms_api_rest.pms_api_rest_utils import url_image_pms_api_rest
from odoo.addons.portal.controllers.portal import CustomerPortal


def is_adult(birthdate):
    if not birthdate:
        return False
    today = datetime.now()
    age = (
        today.year
        - birthdate.year
        - ((today.month, today.day) < (birthdate.month, birthdate.day))
    )
    return age >= 18


def remove_html_tags(text):
    pattern = re.compile(r"<.*?>")
    text_clean = re.sub(pattern, "", text)
    return text_clean


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
                partnerName=reservation.partner_name or None,
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
                children=reservation.children if reservation.children else 0,
                readyForCheckin=reservation.ready_for_checkin,
                checkinPartnerCount=reservation.checkin_partner_count,
                allowedCheckout=reservation.allowed_checkout,
                isSplitted=reservation.splitted,
                pendingCheckinData=reservation.pending_checkin_data,
                createDate=reservation.create_date.isoformat(),
                createdBy=reservation.create_uid.name,
                segmentationId=reservation.segmentation_ids[0].id
                if reservation.segmentation_ids
                else None,
                toAssign=reservation.to_assign,
                reservationType=reservation.reservation_type,
                priceTotal=round(reservation.price_room_services_set, 2),
                priceTax=round(reservation.price_tax, 2),
                discount=round(reservation.discount, 2),
                servicesDiscount=round(reservation.services_discount, 2),
                commissionAmount=round(reservation.commission_amount, 2)
                if reservation.commission_amount
                else None,
                commissionPercent=round(reservation.commission_percent, 2)
                if reservation.commission_percent
                else None,
                priceOnlyServices=round(reservation.price_services, 2),
                priceOnlyRoom=round(reservation.price_total, 2),
                partnerRequests=reservation.partner_requests
                if reservation.partner_requests
                else None,
                nights=reservation.nights,
                numServices=len(reservation.service_ids)
                if reservation.service_ids
                else 0,
                isReselling=any(
                    line.is_reselling for line in reservation.reservation_line_ids
                ),
                isBlocked=reservation.blocked,
            )
        return res

    def _create_vals_from_params(
        self, reservation_vals, reservation_data, reservation_id
    ):
        if reservation_data.preferredRoomId:
            reservation_vals.update(
                {"preferred_room_id": reservation_data.preferredRoomId}
            )
        if reservation_data.boardServiceId is not None:
            reservation_vals.update(
                {"board_service_room_id": reservation_data.boardServiceId or False}
            )
        if reservation_data.pricelistId:
            reservation_vals.update({"pricelist_id": reservation_data.pricelistId})
        if reservation_data.adults:
            reservation_vals.update({"adults": reservation_data.adults})
        if reservation_data.children is not None:
            reservation_vals.update({"children": reservation_data.children})
        if reservation_data.segmentationId is not None:
            if reservation_data.segmentationId != 0:
                reservation_vals.update(
                    {"segmentation_ids": [(6, 0, [reservation_data.segmentationId])]}
                )
            else:
                reservation_vals.update({"segmentation_ids": [(5, 0, 0)]})
        if reservation_data.checkin:
            reservation_vals.update({"checkin": reservation_data.checkin})
        if reservation_data.checkout:
            reservation_vals.update({"checkout": reservation_data.checkout})

        return reservation_vals

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
        self._update_reservation_state(reservation, reservation_data)

        reservation_vals = self._create_vals_from_params(
            reservation_vals,
            reservation_data,
            reservation_id,
        )

        service_cmds = []
        if (
            reservation_data.boardServiceId is not None
            or reservation_data.boardServices is not None
        ):
            for service in reservation.service_ids.filtered(
                lambda x: x.is_board_service
            ):
                service_cmds.append((2, service.id))

        if reservation_data.boardServices is not None:
            for bs in reservation_data.boardServices:
                service_line_cmds = []
                for line in bs.serviceLines:
                    service_line_cmds.append(
                        (
                            0,
                            False,
                            {
                                "price_unit": line.priceUnit,
                                "date": line.date,
                                "discount": line.discount,
                                "day_qty": line.quantity,
                                "auto_qty": True,
                            },
                        )
                    )
                service_cmds.append(
                    (
                        0,
                        False,
                        {
                            "product_id": bs.productId,
                            "is_board_service": True,
                            "reservation_id": reservation_id,
                            "service_line_ids": service_line_cmds,
                        },
                    )
                )
        if service_cmds:
            reservation_vals.update({"service_ids": service_cmds})

        if reservation_vals and reservation_data.boardServices:
            reservation.with_context(skip_compute_service_ids=True).write(
                reservation_vals
            )
        elif reservation_vals:
            reservation.write(reservation_vals)

    def _update_reservation_state(self, reservation, reservation_data):
        if reservation_data.toAssign is not None and not reservation_data.toAssign:
            reservation.action_assign()
        if reservation_data.stateCode == "cancel":
            reservation.action_cancel()
        if reservation_data.stateCode == "confirm":
            reservation.action_confirm()
        if reservation_data.toCheckout is not None and reservation_data.toCheckout:
            reservation.action_reservation_checkout()
        if reservation_data.undoOnboard:
            reservation.action_undo_onboard()

    def _get_reservation_lines_mapped(self, origin_data, reservation_line=False):
        # Return dict witch reservation.lines values (only modified if line exist,
        # or all pass values if line not exist)
        line_vals = {}
        if origin_data.price and (
            not reservation_line
            or round(origin_data.price, 2) != round(reservation_line.price, 2)
        ):
            line_vals["price"] = origin_data.price
        if origin_data.discount is not None and (
            not reservation_line
            or round(origin_data.discount, 2) != round(reservation_line.discount, 2)
        ):
            line_vals["discount"] = origin_data.discount
        if origin_data.cancelDiscount is not None and (
            not reservation_line
            or round(origin_data.cancelDiscount, 2)
            != round(reservation_line.cancelDiscount, 2)
        ):
            line_vals["cancel_discount"] = origin_data.cancelDiscount
        if origin_data.roomId and (
            not reservation_line or origin_data.roomId != reservation_line.room_id.id
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
                    isReselling=reservation_line.is_reselling,
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
                    reservationId=service.reservation_id,
                    name=service.name or service.product_id.name,
                    productId=service.product_id.id,
                    quantity=service.product_qty,
                    priceTotal=round(service.price_total, 2),
                    priceSubtotal=round(service.price_subtotal, 2),
                    priceTaxes=round(service.price_tax, 2),
                    discount=round(service.discount, 2),
                    isBoardService=service.is_board_service,
                    serviceLines=service_lines,
                    isCancelPenalty=service.is_cancel_penalty,
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
            # .filtered(
            #     lambda ch: ch.state != "dummy"
            # )
            for checkin_partner in reservation.checkin_partner_ids:
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
                        documentExpeditionDate=datetime.combine(
                            checkin_partner.document_expedition_date,
                            datetime.min.time(),
                        ).isoformat()
                        if checkin_partner.document_expedition_date
                        else None,
                        documentSupportNumber=checkin_partner.support_number
                        if checkin_partner.support_number
                        else None,
                        documentCountryId=checkin_partner.document_country_id.id
                        if checkin_partner.document_country_id
                        else None,
                        gender=checkin_partner.gender if checkin_partner.gender else "",
                        birthdate=datetime.combine(
                            checkin_partner.birthdate_date, datetime.min.time()
                        ).isoformat()
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
                        nationality=checkin_partner.nationality_id.id
                        if checkin_partner.nationality_id
                        else None,
                        countryState=checkin_partner.residence_state_id.id
                        if checkin_partner.residence_state_id
                        else None,
                        countryStateName=checkin_partner.residence_state_id.name
                        if checkin_partner.residence_state_id
                        else None,
                        countryId=checkin_partner.residence_country_id.id
                        if checkin_partner.residence_country_id
                        else None,
                        checkinPartnerState=checkin_partner.state,
                        signature=checkin_partner.signature
                        if checkin_partner.signature
                        else None,
                        relationship=checkin_partner.ses_partners_relationship
                        if checkin_partner.ses_partners_relationship
                        else "",
                        responsibleCheckinPartnerId=checkin_partner.ses_related_checkin_partner_id.id
                        if checkin_partner.ses_related_checkin_partner_id
                        else None,
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
        print(pms_checkin_partner_info)
        checkin_partner = self.env["pms.checkin.partner"].search(
            [("id", "=", checkin_partner_id), ("reservation_id", "=", reservation_id)]
        )
        if not checkin_partner:
            raise MissingError(_("Checkin partner not found"))
        if (
            pms_checkin_partner_info.actionOnBoard
            and pms_checkin_partner_info.actionOnBoard is not None
        ):
            checkin_partner.action_on_board()
            return checkin_partner.id
        if not pms_checkin_partner_info.originInputData:
            pms_checkin_partner_info.originInputData = checkin_partner.origin_input_data
        checkin_partner.write(
            self.mapping_checkin_partner_values(
                pms_checkin_partner_info,
                checkin_partner.partner_id.id if checkin_partner.partner_id else False,
            )
        )
        # if not partner_id we need to force compute to create partner
        if not checkin_partner.partner_id:
            checkin_partner._compute_partner_id()
        return checkin_partner.id

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.reservation.search.param", is_list=False),
        output_param=Datamodel("pms.reservation.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservations(self, pms_search_param):
        domain = list()
        res_reservations = []
        if pms_search_param.pmsPropertyId:
            domain.append(("pms_property_id", "=", pms_search_param.pmsPropertyId))
        if pms_search_param.toAssign:
            domain.append(("to_assign", "=", True))
            domain.append(("checkin", ">=", fields.Date.today()))
        if pms_search_param.ids:
            domain.append(("id", "in", pms_search_param.ids))
        if pms_search_param.createDateFrom and pms_search_param.createDateTo:
            domain.append(
                (
                    "create_date",
                    ">=",
                    datetime.strptime(
                        pms_search_param.createDateFrom, "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )
            domain.append(
                (
                    "create_date",
                    "<=",
                    datetime.strptime(
                        pms_search_param.createDateTo, "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )
        if pms_search_param.lastUpdateFrom:
            last_update = fields.Datetime.from_string(pms_search_param.lastUpdateFrom)
            domain.append(("write_date", ">=", last_update))

        reservations = self.env["pms.reservation"].search(domain)
        PmsReservationInfo = self.env.datamodels["pms.reservation.info"]
        if not reservations:
            pass
        else:
            for reservation in reservations:
                res_reservations.append(
                    PmsReservationInfo(
                        id=reservation.id,
                        name=reservation.name,
                        folioId=reservation.folio_id.id,
                        folioSequence=reservation.folio_sequence,
                        partnerName=reservation.partner_name or None,
                        boardServiceId=reservation.board_service_room_id.id
                        if reservation.board_service_room_id
                        else None,
                        saleChannelId=reservation.sale_channel_origin_id.id
                        if reservation.sale_channel_origin_id
                        else None,
                        agencyId=reservation.agency_id.id
                        if reservation.agency_id
                        else None,
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
                )
        return res_reservations

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
                self.mapping_checkin_partner_values(
                    pms_checkin_partner_info,
                    checkin_partner.partner_id.id
                    if checkin_partner.partner_id
                    else False,
                )
            )
            # if not partner_id we need to force compute to create partner
            if not checkin_partner.partner_id:
                checkin_partner._compute_partner_id()
            return checkin_partner.id

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
        checkin_partner = self.env["pms.checkin.partner"].browse(checkin_partner_id)
        if checkin_partner:
            checkin_partner.unlink()

    def mapping_checkin_partner_values(
        self, pms_checkin_partner_info, partner_id=False
    ):
        vals = {
            "firstname": pms_checkin_partner_info.firstname,
            "lastname": pms_checkin_partner_info.lastname,
            "lastname2": pms_checkin_partner_info.lastname2,
            "email": pms_checkin_partner_info.email,
            "mobile": pms_checkin_partner_info.mobile,
            "document_type": pms_checkin_partner_info.documentType,
            "document_number": pms_checkin_partner_info.documentNumber,
            "document_country_id": pms_checkin_partner_info.documentCountryId,
            "support_number": pms_checkin_partner_info.documentSupportNumber,
            "gender": pms_checkin_partner_info.gender,
            "residence_street": pms_checkin_partner_info.residenceStreet,
            "nationality_id": pms_checkin_partner_info.nationality,
            "residence_zip": pms_checkin_partner_info.zip,
            "residence_city": pms_checkin_partner_info.residenceCity,
            "residence_state_id": pms_checkin_partner_info.countryState,
            "residence_country_id": pms_checkin_partner_info.countryId,
            "origin_input_data": pms_checkin_partner_info.originInputData,
        }
        if pms_checkin_partner_info.partnerId != partner_id:
            vals.update({"partner_id": pms_checkin_partner_info.partnerId})
        if pms_checkin_partner_info.documentExpeditionDate:
            document_expedition_date = datetime.strptime(
                pms_checkin_partner_info.documentExpeditionDate, "%d/%m/%Y"
            )
            document_expedition_date = document_expedition_date.strftime("%Y-%m-%d")
            vals.update({"document_expedition_date": document_expedition_date})
        else:
            vals.update({"document_expedition_date": False})
        if pms_checkin_partner_info.birthdate:
            birthdate = datetime.strptime(
                pms_checkin_partner_info.birthdate, "%d/%m/%Y"
            )
            birthdate = birthdate.strftime("%Y-%m-%d")
            vals.update({"birthdate_date": birthdate})
        else:
            vals.update({"birthdate_date": False})
        if pms_checkin_partner_info.signature:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(base64.b64decode(pms_checkin_partner_info.signature))
                temp_path = f.name

            with open(temp_path, "rb") as f:
                signature_image = f.read()
            os.unlink(temp_path)

            vals.update({"signature": base64.b64encode(signature_image)})
        else:
            vals.update({"signature": False})
        if pms_checkin_partner_info.relationship != '':
            vals.update({"ses_partners_relationship": pms_checkin_partner_info.relationship})
        if pms_checkin_partner_info.responsibleCheckinPartnerId:
            vals.update({"ses_related_checkin_partner_id": pms_checkin_partner_info.responsibleCheckinPartnerId})
        return vals

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/checkin-report",
                ],
                "GET",
            )
        ],
        auth="jwt_api_pms",
        output_param=Datamodel("pms.report", is_list=False),
    )
    def print_all_checkins(self, reservation_id):
        reservations = False
        if reservation_id:
            reservations = self.env["pms.reservation"].sudo().browse(reservation_id)
        checkins = reservations.checkin_partner_ids.filtered(
            lambda x: x.state in ["precheckin", "onboard", "done"]
        )
        pdf = (
            self.env.ref("pms.action_traveller_report")
            .sudo()
            ._render_qweb_pdf(checkins.ids)[0]
        )
        base64EncodedStr = base64.b64encode(pdf)
        PmsResponse = self.env.datamodels["pms.report"]
        return PmsResponse(binary=base64EncodedStr)

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/checkin-partners/"
                    "<int:checkin_partner_id>/checkin-report",
                ],
                "GET",
            )
        ],
        auth="jwt_api_pms",
        output_param=Datamodel("pms.report", is_list=False),
    )
    def print_checkin(self, reservation_id, checkin_partner_id):
        reservations = False
        if reservation_id:
            reservations = self.env["pms.reservation"].sudo().browse(reservation_id)
        checkin_partner = reservations.checkin_partner_ids.filtered(
            lambda x: x.id == checkin_partner_id
        )
        pdf = (
            self.env.ref("pms.action_traveller_report")
            .sudo()
            ._render_qweb_pdf(checkin_partner.id)[0]
        )
        base64EncodedStr = base64.b64encode(pdf)
        PmsResponse = self.env.datamodels["pms.report"]
        return PmsResponse(binary=base64EncodedStr)

    @restapi.method(
        [
            (
                [
                    "/kelly-report",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.report.search.param", is_list=False),
        output_param=Datamodel("pms.report", is_list=False),
        auth="jwt_api_pms",
    )
    def kelly_report(self, pms_report_search_param):
        pms_property_id = pms_report_search_param.pmsPropertyId
        date_from = fields.Date.from_string(pms_report_search_param.dateFrom)

        report_wizard = self.env["kellysreport"].create(
            {
                "date_start": date_from,
                "pms_property_id": pms_property_id,
            }
        )
        report_wizard.calculate_report()
        result = report_wizard._excel_export()
        file_name = result["xls_filename"]
        base64EncodedStr = result["xls_binary"]
        PmsResponse = self.env.datamodels["pms.report"]
        return PmsResponse(fileName=file_name, binary=base64EncodedStr)

    @restapi.method(
        [
            (
                [
                    "/arrivals-report",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.report.search.param", is_list=False),
        output_param=Datamodel("pms.report", is_list=False),
        auth="jwt_api_pms",
    )
    def arrivals_report(self, pms_report_search_param):
        pms_property_id = pms_report_search_param.pmsPropertyId
        date_from = fields.Date.from_string(pms_report_search_param.dateFrom)

        query = self.env.ref("pms_api_rest.sql_export_arrivals")
        if not query:
            raise MissingError(_("SQL query not found"))
        report_wizard = self.env["sql.file.wizard"].create({"sql_export_id": query.id})
        if not report_wizard._fields.get(
            "x_date_from"
        ) or not report_wizard._fields.get("x_pms_property_id"):
            raise MissingError(
                _("The Query params was modifieds, please contact the administrator")
            )
        report_wizard.x_date_from = date_from
        report_wizard.x_pms_property_id = pms_property_id

        report_wizard.export_sql()
        file_name = report_wizard.file_name
        base64EncodedStr = report_wizard.binary_file
        PmsResponse = self.env.datamodels["pms.report"]
        return PmsResponse(fileName=file_name, binary=base64EncodedStr)

    @restapi.method(
        [
            (
                [
                    "/departures-report",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.report.search.param", is_list=False),
        output_param=Datamodel("pms.report", is_list=False),
        auth="jwt_api_pms",
    )
    def departures_report(self, pms_report_search_param):
        pms_property_id = pms_report_search_param.pmsPropertyId
        date_from = fields.Date.from_string(pms_report_search_param.dateFrom)

        query = self.env.ref("pms_api_rest.sql_export_departures")
        if not query:
            raise MissingError(_("SQL query not found"))
        if query.state == "draft":
            query.button_validate_sql_expression()
        report_wizard = self.env["sql.file.wizard"].create({"sql_export_id": query.id})
        if not report_wizard._fields.get(
            "x_date_from"
        ) or not report_wizard._fields.get("x_pms_property_id"):
            raise MissingError(
                _("The Query params was modifieds, please contact the administrator")
            )
        report_wizard.x_date_from = date_from
        report_wizard.x_pms_property_id = pms_property_id

        report_wizard.export_sql()
        file_name = report_wizard.file_name
        base64EncodedStr = report_wizard.binary_file
        PmsResponse = self.env.datamodels["pms.report"]
        return PmsResponse(fileName=file_name, binary=base64EncodedStr)

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/wizard-states",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.wizard.state.info", is_list=False),
        auth="jwt_api_pms",
    )
    def wizard_states(self, reservation_id):
        reservation = self.env["pms.reservation"].search([("id", "=", reservation_id)])
        today = datetime.now().strftime("%Y-%m-%d")
        wizard_states = [
            {
                "code": "overbooking_with_availability",
                "title": "Overbooking",
                "domain": "["
                "('state', 'in', ['draft', 'confirm', 'arrival_delayed']), "
                "('overbooking', '=', True), "
                f"('checkin', '>=', '{today}'),"
                "('reservation_type', 'in', ['normal', 'staff'])"
                "]",
                "filtered": "lambda r: r.count_alternative_free_rooms",
                "text": f"Parece que ha entrado una reserva sin haber disponibilidad para {reservation.sudo().room_type_id.name}.",
                "priority": 100,
            },
            {
                "code": "overbooking_without_availability",
                "title": "Overbooking",
                "domain": "["
                "('state', 'in', ['draft', 'confirm', 'arrival_delayed']), "
                "('overbooking', '=', True), "
                f"('checkin', '>=', '{today}'),"
                "('reservation_type', 'in', ['normal', 'staff'])"
                "]",
                "filtered": "lambda r: r.count_alternative_free_rooms <= 0",
                "text": f"Parece que ha entrado una reserva sin haber disponibilidad para {reservation.room_type_id.name}."
                f"Por desgracia no parece que hay ninguna "
                f"habitación disponible con la capacidad suficiente para esta reserva",
                "priority": 150,
            },
            {
                "code": "splitted_without_availability",
                "title": "Divididas",
                "domain": "[('state', 'in', ['draft', 'confirm', 'arrival_delayed']),"
                "('splitted', '=', True),"
                f"('checkin', '>=', '{today}'),"
                "('reservation_type', 'in', ['normal', 'staff'])"
                "]",
                "filtered": "lambda r: r.count_alternative_free_rooms <= 0",
                "text": f"Parece que a {reservation.partner_name} le ha tocado dormir en habitaciones diferentes "
                f" pero no hay ninguna habitación disponible para asignarle, puedes probar a mover otras reservas "
                f" para poder establecerle una única habitación.  ",
                "priority": 200,
            },
            {
                "code": "splitted_with_availability",
                "title": "Divididas",
                "domain": "[('state', 'in', ['draft', 'confirm', 'arrival_delayed']),"
                "('splitted', '=', True),"
                f"('checkin', '>=', '{today}'),"
                "('reservation_type', 'in', ['normal', 'staff'])"
                "]",
                "filtered": "lambda r: r.count_alternative_free_rooms",
                "text": f"Parece que a {reservation.partner_name} le ha tocado dormir en habitaciones diferentes"
                f" pero tienes la posibilidad de moverlo a {reservation.count_alternative_free_rooms} "
                f" {' habitación' if reservation.count_alternative_free_rooms == 1 else ' habitaciones'}.",
                "priority": 220,
            },
            {
                "code": "to_assign",
                "title": "Por asignar",
                "domain": "[('state', 'in', ['draft', 'confirm', 'arrival_delayed']),"
                "('to_assign', '=', True),"
                "('reservation_type', 'in', ['normal', 'staff']),"
                f"('checkin', '>=', '{today}'),"
                "]",
                "text": f"La reserva de {reservation.partner_name} ha sido asignada a la habitación {reservation.preferred_room_id.name},"
                " puedes confirmar la habitación o cambiar a otra desde aquí.",
                "priority": 300,
            },
            {
                "code": "to_confirm",
                "title": "Por confirmar",
                "domain": "[('state', '=', 'draft'),"
                f"('checkin', '>=', '{today}'),"
                "('reservation_type', 'in', ['normal', 'staff']),"
                "]",
                "text": f"La reserva de {reservation.partner_name} está pendiente de confirmar, puedes confirmarla desde aquí.",
                "priority": 400,
            },
            {
                "code": "checkin_done_precheckin",
                "title": "Entrada Hoy",
                "domain": "[('state', '=',  'confirm'),"
                f"('checkin', '=', '{today}'),"
                "('pending_checkin_data', '=', 0),"
                "('reservation_type', 'in', ['normal', 'staff'])"
                "]",
                "text": "Todos los huéspedes de esta reserva tienen los datos registrados, "
                " puedes marcar la entrada directamente desde aquí",
                "priority": 500,
            },
            {
                "code": "checkin_partial_precheckin",
                "title": "Entrada Hoy",
                "domain": "[('state', '=',  'confirm'),"
                f"('checkin', '=', '{today}'),"
                "('pending_checkin_data', '>', 0),"
                "('checkin_partner_ids.state','=', 'precheckin'),"
                "('reservation_type', 'in', ['normal', 'staff'])"
                "]",
                "text": f"Faltan {reservation.pending_checkin_data} {' huésped ' if reservation.pending_checkin_data == 1 else ' huéspedes '} "
                f"por registrar sus datos.Puedes abrir el asistente de checkin "
                f" para completar los datos.",
                "priority": 530,
            },
            {
                "code": "checkin_no_precheckin",
                "title": "Entrada Hoy",
                "domain": "[('state', '=', 'confirm'),"
                f"('checkin', '=', '{today}'),"
                "('pending_checkin_data', '>', 0),"
                "('reservation_type', 'in', ['normal', 'staff'])"
                "]",
                "filtered": "lambda r: all([c.state in ('draft','dummy') for c in r.checkin_partner_ids]) ",
                "text": "Registra los datos de los huéspedes desde el asistente del checkin.",
                "priority": 580,
            },
            {
                "code": "confirmed_without_payment_and_precheckin",
                "title": "Confirmadas a futuro sin pagar y sin precheckin realizado",
                "domain": "[('state', 'in', ['draft', 'confirm', 'arrival_delayed']),"
                "('reservation_type', 'in', ['normal', 'staff']),"
                f"('checkin', '>', '{today}'),"
                "('pending_checkin_data', '>', 0),"
                "('folio_payment_state', 'in', ['not_paid', 'partial'])"
                "]",
                "text": "Esta reserva está pendiente de cobro y de que los huéspedes "
                " registren sus datos: puedes enviarles un recordatorio desde aquí",
                "priority": 600,
            },
            {
                "code": "confirmed_without_payment",
                "title": "Confirmadas a futuro sin pagar",
                "domain": "[('state', 'in', ['draft', 'confirm', 'arrival_delayed']),"
                "('reservation_type', 'in', ['normal', 'staff']),"
                f"('checkin', '>', '{today}'),"
                "('pending_checkin_data', '=', 0),"
                "('folio_payment_state', 'in', ['not_paid', 'partial'])"
                "]",
                "text": "Esta reserva está pendiente de cobro, puedes enviarle sun recordatorio desde aquí",
                "priority": 630,
            },
            {
                "code": "confirmed_without_precheckin",
                "title": "Confirmadas a futuro sin pagar",
                "domain": "[('state', 'in', ['draft', 'confirm', 'arrival_delayed']),"
                "('reservation_type', 'in', ['normal', 'staff']),"
                f"('checkin', '>', '{today}'),"
                "('pending_checkin_data', '>', 0),"
                "('folio_payment_state', 'in', ['paid', 'overpayment','nothing_to_pay'])"
                "]",
                "text": "Esta reserva no tiene los datos de los huéspedes registrados, puedes enviarles un recordatorio desde aquí",
                "priority": 660,
            },
            {
                "code": "cancelled",
                "title": "Cancelada con cargos y sin cobrar",
                "domain": "[('state', '=', 'cancel'),"
                "('cancelled_reason', 'in',['late','noshow']),"
                "('folio_payment_state', 'in', ['not_paid', 'partial']),"
                "]",
                "filtered": "lambda r: r.service_ids.filtered(lambda s: s.is_cancel_penalty and s.price_total > 0)",
                "text": f"La reserva de {reservation.partner_name} ha sido cancelada con una penalización de {reservation.service_ids.filtered(lambda s: s.is_cancel_penalty).price_total}€,"
                " puedes eliminar la penalización en caso de que no se vaya a cobrar.",
                "priority": 700,
            },
            {
                "code": "onboard_without_payment",
                "title": "Por cobrar dentro",
                "domain": "[('state', 'in', ['onboard', 'departure_delayed']),"
                "('folio_payment_state', 'in', ['not_paid', 'partial'])"
                "]",
                "text": f"En esta reserva tenemos un pago pendiente de {reservation.folio_pending_amount}. Puedes registrar el pago desde aquí.",
                "priority": 800,
            },
            {
                "code": "done_without_payment",
                "title": "Por cobrar pasadas",
                "domain": "[('state', '=', 'done'),"
                "('folio_payment_state', 'in', ['not_paid', 'partial'])"
                "]",
                "text": f"Esta reserva ha quedado con un cargo pendiente de {reservation.folio_pending_amount}€."
                " Cuando gestiones el cobro puedes registrarlo desde aquí.",
                "priority": 900,
            },
            {
                "code": "checkout",
                "title": "Checkout",
                "domain": "[('state', 'in', ['onboard', 'departure_delayed']),"
                f"('checkout', '=', '{today}'),"
                "]",
                "text": "Reserva lista para el checkout, marca la salida directamente desde aquí.",
                "priority": 1000,
            },
        ]
        # We order the states by priority and return the first
        # state whose domain meets the reservation;
        # if the state also has the key 'filtered,'
        # it must also meet that filter.

        sorted_wizard_states = sorted(wizard_states, key=lambda x: x["priority"])
        PmsWizardStateInfo = self.env.datamodels["pms.wizard.state.info"]
        for state in sorted_wizard_states:
            domain = expression.AND(
                [[("id", "=", reservation_id)], safe_eval(state["domain"])]
            )
            if self.env["pms.reservation"].search_count(domain):
                if state.get("filtered") and not self.env["pms.reservation"].browse(
                    reservation_id
                ).filtered(safe_eval(state["filtered"])):
                    continue

                return PmsWizardStateInfo(
                    code=state["code"],
                    title=state["title"],
                    text=state["text"],
                )

        return PmsWizardStateInfo(
            code="",
            title="",
            text="",
        )

    # PUBLIC ENDPOINTS
    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/precheckin/<string:token>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.folio.public.info", is_list=False),
        auth="public",
    )
    def get_reservation_public_info(self, reservation_id, token):
        # variable initialization
        folio_room_types_description_list = list()
        folio_checkin_partner_names = list()
        num_checkins = 0

        # check if the folio exists
        reservation_record = self.env["pms.reservation"].sudo().browse(reservation_id)
        if not reservation_record.exists():
            raise MissingError(_("Reservation not found"))

        # check if the reservation is accessible
        try:
            reservation_record = CustomerPortal._document_check_access(
                self,
                "pms.reservation",
                reservation_id,
                access_token=token,
            )
        except AccessError:
            raise MissingError(_("Reservation not found"))

        reservation_checkin_partner_names = []
        reservation_checkin_partners = []
        num_checkins += len(reservation_record.checkin_partner_ids)
        folio_room_types_description_list.append(reservation_record.room_type_id.name)

        # iterate checkin partner names completed
        for checkin_partner in reservation_record.checkin_partner_ids:
            reservation_checkin_partners.append(
                self.env.datamodels["pms.checkin.partner.info"](
                    id=checkin_partner.id,
                    checkinPartnerState=checkin_partner.state,
                )
            )
            is_mandatory_fields = True
            for field in self.env["pms.checkin.partner"]._checkin_mandatory_fields():
                if not getattr(checkin_partner, field):
                    is_mandatory_fields = False
                    break
            if is_mandatory_fields:
                reservation_checkin_partner_names.append(checkin_partner.firstname)
                folio_checkin_partner_names.append(checkin_partner.firstname)

        # append reservation public info
        reservations = [
            self.env.datamodels["pms.reservation.public.info"](
                roomTypeName=reservation_record.room_type_id.name,
                checkinNamesCompleted=reservation_checkin_partner_names,
                nights=reservation_record.nights,
                checkin=datetime.combine(
                    reservation_record.checkin, datetime.min.time()
                ).isoformat(),
                checkout=datetime.combine(
                    reservation_record.checkout, datetime.min.time()
                ).isoformat(),
                adults=reservation_record.adults,
                children=reservation_record.children,
                reservationReference=reservation_record.name,
                checkinPartners=reservation_checkin_partners,
                reservationAmount=reservation_record.price_total,
            )
        ]
        ine_category = ""
        if reservation_record.pms_property_id.ine_category_id:
            ine_category = (
                reservation_record.pms_property_id.ine_category_id.category
                + " ("
                + reservation_record.pms_property_id.ine_category_id.type
                + ")"
            )

        return self.env.datamodels["pms.folio.public.info"](
            pmsPropertyName=reservation_record.pms_property_id.name,
            pmsPropertyStreet=reservation_record.pms_property_id.street,
            pmsPropertyCity=reservation_record.pms_property_id.city,
            pmsPropertyZip=reservation_record.pms_property_id.zip,
            pmsPropertyState=reservation_record.pms_property_id.state_id.name,
            pmsPropertyPhoneNumber=reservation_record.pms_property_id.phone,
            pmsPropertyLogo=url_image_pms_api_rest(
                "pms.property",
                reservation_record.pms_property_id.id,
                "logo",
            ),
            pmsPropertyIneCategory=ine_category,
            pmsPropertyImage=url_image_pms_api_rest(
                "pms.property",
                reservation_record.pms_property_id.id,
                "hotel_image_pms_api_rest",
            ),
            pmsPropertyIsOCRAvailable=True
            if reservation_record.pms_property_id.ocr_checkin_supplier
            else False,
            pmsPropertyPrivacyPolicy=remove_html_tags(
                reservation_record.pms_property_id.privacy_policy
            )
            if reservation_record.pms_property_id.privacy_policy
            else "",
            pmsCompanyName=reservation_record.pms_property_id.company_id.name,
            pmsPropertyId=reservation_record.pms_property_id.id,
            folioPartnerName=reservation_record.folio_id.partner_name,
            reservations=reservations,
            cardexWarning=reservation_record.pms_property_id.cardex_warning
            if reservation_record.pms_property_id.cardex_warning
            else "",
        )

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/precheckin-reservation/<string:token>"
                    "/partner/<string:documentType>/<string:documentNumber>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.partner.info", is_list=True),
        auth="public",
    )
    def get_checkin_partner_by_doc_number(
        self, reservation_id, token, document_type, document_number
    ):
        reservation_record = self.env["pms.reservation"].sudo().browse(reservation_id)
        if not reservation_record:
            raise MissingError(_("Folio not found"))
        # check if the reservation is accessible
        try:
            CustomerPortal._document_check_access(
                self,
                "pms.reservation",
                reservation_record.id,
                access_token=token,
            )
        except AccessError:
            raise MissingError(_("Reservation not found"))

        doc_type = (
            self.env["res.partner.id_category"]
            .sudo()
            .search([("id", "=", document_type)])
        )
        # Clean Document number
        document_number = re.sub(r"[^a-zA-Z0-9]", "", document_number).upper()
        partner = (
            self.env["pms.checkin.partner"]
            .sudo()
            ._get_partner_by_document(document_number, doc_type)
        )
        partners = []
        if partner:
            doc_record = partner.id_numbers.filtered(
                lambda doc: doc.category_id.id == doc_type.id
            )
            PmsCheckinPartnerInfo = self.env.datamodels["pms.checkin.partner.info"]

            document_numbers_in_reservation = (
                reservation_record.checkin_partner_ids.filtered(
                    lambda x: x.document_type.id == doc_type.id
                    and x.document_number == document_number
                )
            )

            partners.append(
                PmsCheckinPartnerInfo(
                    # partner id
                    id=partner.id,
                    # names
                    firstname="#" if partner.firstname else None,
                    lastname="#" if partner.lastname else None,
                    lastname2="#" if partner.lastname2 else None,
                    # contact
                    email="#" if partner.email else None,
                    mobile="#" if partner.mobile else None,
                    # document info
                    documentCountryId=doc_record.country_id.id
                    if doc_record.country_id.id
                    else None,
                    documentType=doc_type.id if doc_type.id else None,
                    documentNumber="#" if doc_record.name else None,
                    documentExpeditionDate=datetime.utcfromtimestamp(0).isoformat()
                    if doc_record.valid_from
                    else None,
                    documentSupportNumber="#" if doc_record.support_number else None,
                    # personal info
                    gender="#" if partner.gender else None,
                    birthdate=datetime.utcfromtimestamp(0).isoformat()
                    if partner.birthdate_date
                    else None,
                    # nationality
                    nationality=-1 if partner.nationality_id.id else None,
                    # residence info
                    countryId=partner.residence_country_id
                    if partner.residence_country_id
                    else None,
                    residenceStreet="#" if partner.residence_street else None,
                    zip="#" if partner.residence_zip else None,
                    residenceCity="#" if partner.residence_city else None,
                    countryState=-1 if partner.residence_state_id.id else None,
                    # is already in reservation
                    isAlreadyInReservation=True
                    if document_numbers_in_reservation
                    else False,
                )
            )
        return partners

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/precheckin-reservation/<string:token>"
                    "/checkin-partners/<int:checkin_partner_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.checkin.partner.info", is_list=False),
        auth="public",
    )
    def patch_checkin_partner(
        self, reservation_id, token, checkin_partner_id, pms_checkin_partner_info
    ):
        reservation_record = self.env["pms.reservation"].sudo().browse(reservation_id)
        if not reservation_record:
            raise MissingError(_("Folio not found"))
        # check if the reservation is accessible
        try:
            CustomerPortal._document_check_access(
                self,
                "pms.reservation",
                reservation_record.id,
                access_token=token,
            )
        except AccessError:
            raise MissingError(_("Reservation not found"))

        partner_record = False
        # search checkin partner by id
        checkin_partner_record = (
            self.env["pms.checkin.partner"].sudo().browse(checkin_partner_id)
        )
        if pms_checkin_partner_info.partnerId:
            # search partner by api_rest_id
            partner_record = (
                self.env["res.partner"]
                .sudo()
                .browse(pms_checkin_partner_info.partnerId)
            )

        # partner
        if partner_record:
            checkin_partner_record.partner_id = partner_record.id
        # document info
        if pms_checkin_partner_info.documentCountryId:
            checkin_partner_record.document_country_id = (
                pms_checkin_partner_info.documentCountryId
            )
        if (
            pms_checkin_partner_info.documentNumber
            and pms_checkin_partner_info.documentType
        ):
            checkin_partner_record.write(
                {
                    "document_type": pms_checkin_partner_info.documentType,
                    "document_number": pms_checkin_partner_info.documentNumber,
                }
            )
        if pms_checkin_partner_info.documentExpeditionDate:
            checkin_partner_record.document_expedition_date = (
                pms_checkin_partner_info.documentExpeditionDate
            )
        if pms_checkin_partner_info.documentSupportNumber:
            checkin_partner_record.support_number = (
                pms_checkin_partner_info.documentSupportNumber
            )
        # name
        if pms_checkin_partner_info.firstname:
            checkin_partner_record.firstname = pms_checkin_partner_info.firstname
        if pms_checkin_partner_info.lastname:
            checkin_partner_record.lastname = pms_checkin_partner_info.lastname
        if pms_checkin_partner_info.lastname2:
            checkin_partner_record.lastname2 = pms_checkin_partner_info.lastname2
        # personal info
        if pms_checkin_partner_info.birthdate:
            checkin_partner_record.birthdate_date = pms_checkin_partner_info.birthdate
        if pms_checkin_partner_info.gender:
            checkin_partner_record.gender = pms_checkin_partner_info.gender
        # nationality
        if pms_checkin_partner_info.nationality:
            checkin_partner_record.nationality_id = pms_checkin_partner_info.nationality
        # residence info
        if pms_checkin_partner_info.countryId:
            checkin_partner_record.residence_country_id = (
                pms_checkin_partner_info.countryId
            )
        if pms_checkin_partner_info.zip:
            checkin_partner_record.residence_zip = pms_checkin_partner_info.zip
        if pms_checkin_partner_info.residenceCity:
            checkin_partner_record.residence_city = (
                pms_checkin_partner_info.residenceCity
            )
        if pms_checkin_partner_info.countryState:
            checkin_partner_record.residence_state_id = (
                pms_checkin_partner_info.countryState
            )
        if pms_checkin_partner_info.residenceStreet:
            checkin_partner_record.residence_street = (
                pms_checkin_partner_info.residenceStreet
            )
        # contact
        if pms_checkin_partner_info.email:
            checkin_partner_record.email = pms_checkin_partner_info.email
        if pms_checkin_partner_info.mobile:
            checkin_partner_record.mobile = pms_checkin_partner_info.mobile
        # signature
        if pms_checkin_partner_info.signature:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(base64.b64decode(pms_checkin_partner_info.signature))
                temp_path = f.name

            with open(temp_path, "rb") as f:
                signature_image = f.read()
            os.unlink(temp_path)

            checkin_partner_record.signature = base64.b64encode(signature_image)
        else:
            checkin_partner_record.signature = False
        # legal representative
        if (
            pms_checkin_partner_info.documentLegalRepresentative
            and pms_checkin_partner_info.relationship
        ):
            record_checkin_partner_legal_representative = (
                self.env["pms.checkin.partner"]
                .sudo()
                .search(
                    [
                        (
                            "document_number",
                            "=",
                            pms_checkin_partner_info.documentLegalRepresentative,
                        )
                    ]
                )
            )
            if record_checkin_partner_legal_representative:
                checkin_partner_record.write(
                    {
                        "ses_related_checkin_partner_id": record_checkin_partner_legal_representative.id,
                        "ses_partners_relationship": pms_checkin_partner_info.relationship,
                    }
                )

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/precheckin/<string:token>/folio-adults",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.checkin.partner.info", is_list=False),
        auth="public",
    )
    def are_there_adults_registered_in_folio(
        self, reservation_id, token, checkin_partner_search_params
    ):
        # check if the reservation exists
        reservation_record = self.env["pms.reservation"].sudo().browse(reservation_id)
        if not reservation_record.exists():
            raise MissingError(_("Reservation not found"))

        # check if the reservation is accessible
        try:
            CustomerPortal._document_check_access(
                self,
                "pms.reservation",
                reservation_record.id,
                access_token=token,
            )
        except AccessError:
            raise MissingError(_("Folio not found"))

        if checkin_partner_search_params.documentNumber:
            adults = reservation_record.folio_id.checkin_partner_ids.filtered(
                lambda x: x.document_number
                == checkin_partner_search_params.documentNumber
                and is_adult(x.birthdate_date)
            )
            if adults:
                rdo = True
            else:
                rdo = False
        else:
            adults = reservation_record.folio_id.checkin_partner_ids.filtered(
                lambda x: is_adult(x.birthdate_date)
            )
            if adults:
                rdo = True
            else:
                rdo = False
        return rdo
