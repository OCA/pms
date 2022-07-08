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
            # services = []
            # for service in reservation.service_ids:
            #     if service.is_board_service:
            #         services.append(
            #             {
            #                 "id": service.id,
            #                 "name": service.name,
            #                 "quantity": service.product_qty,
            #                 "priceTotal": service.price_total,
            #                 "priceSubtotal": service.price_subtotal,
            #                 "priceTaxes": service.price_tax,
            #                 "discount": service.discount,
            #             }
            #         )
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
                partnerName=reservation.partner_name,
                boardServiceId=reservation.board_service_room_id.id or None,
                saleChannelId=reservation.channel_type_id.id or None,
                agencyId=reservation.agency_id.id or None,
                checkin=datetime.combine(
                    reservation.checkin, datetime.min.time()
                ).isoformat(),
                checkout=datetime.combine(
                    reservation.checkout, datetime.min.time()
                ).isoformat(),
                arrivalHour=reservation.arrival_hour,
                departureHour=reservation.departure_hour,
                roomTypeId=reservation.room_type_id.id or None,
                preferredRoomId=reservation.preferred_room_id.id or None,
                pricelistId=reservation.pricelist_id.id,
                adults=reservation.adults,
                overbooking=reservation.overbooking,
                externalReference=reservation.external_reference or None,
                state=dict(reservation.fields_get(["state"])["state"]["selection"])[
                    reservation.state
                ],
                children=reservation.children or None,
                readyForCheckin=reservation.ready_for_checkin,
                allowedCheckout=reservation.allowed_checkout,
                isSplitted=reservation.splitted,
                pendingCheckinData=reservation.pending_checkin_data,
                createDate=datetime.combine(
                    reservation.create_date, datetime.min.time()
                ).isoformat(),
                segmentationId=reservation.segmentation_ids[0].id
                if reservation.segmentation_ids
                else None,
                cancellationPolicyId=reservation.pricelist_id.cancelation_rule_id.id
                or None,
                toAssign=reservation.to_assign,
                reservationType=reservation.reservation_type,
                priceTotal=reservation.price_room_services_set,
                discount=reservation.discount,
                commissionAmount=reservation.commission_amount or None,
                priceOnlyServices=reservation.price_services,
                priceOnlyRoom=reservation.price_total,
            )
        return res

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.reservation.updates", is_list=False),
        auth="jwt_api_pms",
    )
    def update_reservation(self, reservation_id, reservation_lines_changes):
        if reservation_lines_changes.reservationLinesChanges:

            # get date of first reservation id to change
            first_reservation_line_id_to_change = (
                reservation_lines_changes.reservationLinesChanges[0][
                    "reservationLineId"
                ]
            )
            first_reservation_line_to_change = self.env["pms.reservation.line"].browse(
                first_reservation_line_id_to_change
            )
            date_first_reservation_line_to_change = datetime.strptime(
                reservation_lines_changes.reservationLinesChanges[0]["date"], "%Y-%m-%d"
            )

            # iterate changes
            for change_iterator in sorted(
                reservation_lines_changes.reservationLinesChanges,
                # adjust order to start changing from last/first reservation line
                # to avoid reservation line date constraint
                reverse=first_reservation_line_to_change.date
                < date_first_reservation_line_to_change.date(),
                key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"),
            ):
                # recordset of each line
                line_to_change = self.env["pms.reservation.line"].search(
                    [
                        ("reservation_id", "=", reservation_id),
                        ("id", "=", change_iterator["reservationLineId"]),
                    ]
                )
                # modifying date, room_id, ...
                if "date" in change_iterator:
                    line_to_change.date = change_iterator["date"]
                if (
                    "roomId" in change_iterator
                    and line_to_change.room_id.id != change_iterator["roomId"]
                ):
                    line_to_change.room_id = change_iterator["roomId"]

            max_value = max(
                first_reservation_line_to_change.reservation_id.reservation_line_ids.mapped(
                    "date"
                )
            ) + timedelta(days=1)
            min_value = min(
                first_reservation_line_to_change.reservation_id.reservation_line_ids.mapped(
                    "date"
                )
            )
            reservation = self.env["pms.reservation"].browse(reservation_id)
            reservation.checkin = min_value
            reservation.checkout = max_value

        else:
            reservation_to_update = (
                self.env["pms.reservation"].sudo().search([("id", "=", reservation_id)])
            )
            reservation_vals = {}

            if reservation_lines_changes.preferredRoomId:
                reservation_vals.update(
                    {"preferred_room_id": reservation_lines_changes.preferredRoomId}
                )
            if reservation_lines_changes.boardServiceId:
                reservation_vals.update(
                    {"board_service_room_id": reservation_lines_changes.boardServiceId}
                )
            if reservation_lines_changes.pricelistId:
                reservation_vals.update(
                    {"pricelist_id": reservation_lines_changes.pricelistId}
                )
            if reservation_lines_changes.adults:
                reservation_vals.update({"adults": reservation_lines_changes.adults})
            if reservation_lines_changes.children:
                reservation_vals.update(
                    {"children": reservation_lines_changes.children}
                )
            if reservation_lines_changes.segmentationId:
                reservation_vals.update(
                    {
                        "segmentation_ids": [
                            (6, 0, [reservation_lines_changes.segmentationId])
                        ]
                    }
                )
            reservation_to_update.write(reservation_vals)

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
                    price=reservation_line.price,
                    discount=reservation_line.discount,
                    cancelDiscount=reservation_line.cancel_discount,
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
                    "/<int:_reservation_id>/reservation-lines/<int:reservation_line_id>",
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
                        else "",
                        lastname=checkin_partner.lastname
                        if checkin_partner.lastname
                        else "",
                        lastname2=checkin_partner.lastname2
                        if checkin_partner.lastname2
                        else "",
                        email=checkin_partner.email if checkin_partner.email else "",
                        mobile=checkin_partner.mobile if checkin_partner.mobile else "",
                        documentType=checkin_partner.document_type.id
                        if checkin_partner.document_type
                        else -1,
                        documentNumber=checkin_partner.document_number
                        if checkin_partner.document_number
                        else "",
                        documentExpeditionDate=document_expedition_date
                        if checkin_partner.document_expedition_date
                        else "",
                        documentSupportNumber=checkin_partner.support_number
                        if checkin_partner.support_number
                        else "",
                        gender=checkin_partner.gender if checkin_partner.gender else "",
                        birthdate=birthdate_date
                        if checkin_partner.birthdate_date
                        else "",
                        residenceStreet=checkin_partner.residence_street
                        if checkin_partner.residence_street
                        else "",
                        zip=checkin_partner.residence_zip
                        if checkin_partner.residence_zip
                        else "",
                        residenceCity=checkin_partner.residence_city
                        if checkin_partner.residence_city
                        else "",
                        nationality=checkin_partner.residence_country_id.id
                        if checkin_partner.residence_country_id
                        else -1,
                        countryState=checkin_partner.residence_state_id.id
                        if checkin_partner.residence_state_id
                        else -1,
                        checkinPartnerState=checkin_partner.state,
                    )
                )
        return checkin_partners

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/checkin-partners/<int:checkin_partner_id>",
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
                self._get_checkin_partner_values(pms_checkin_partner_info)
            )

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
                self._get_checkin_partner_values(pms_checkin_partner_info)
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

    def _get_checkin_partner_values(self, pms_checkin_partner_info):
        vals = dict()
        if pms_checkin_partner_info.firstname:
            vals.update({"firstname": pms_checkin_partner_info.firstname})
        if pms_checkin_partner_info.lastname:
            vals.update({"lastname": pms_checkin_partner_info.lastname})
        if pms_checkin_partner_info.lastname2:
            vals.update({"lastname2": pms_checkin_partner_info.lastname2})
        if pms_checkin_partner_info.email:
            vals.update({"email": pms_checkin_partner_info.email})
        if pms_checkin_partner_info.mobile:
            vals.update({"mobile": pms_checkin_partner_info.mobile})
        if (
            pms_checkin_partner_info.documentType
            and pms_checkin_partner_info.documentType != -1
        ):
            document_type = pms_checkin_partner_info.documentType
            vals.update({"document_type": document_type})
        if pms_checkin_partner_info.documentNumber:
            vals.update({"document_number": pms_checkin_partner_info.documentNumber})
        if pms_checkin_partner_info.documentExpeditionDate:
            document_expedition_date = datetime.strptime(
                pms_checkin_partner_info.documentExpeditionDate, "%d/%m/%Y"
            )
            document_expedition_date = document_expedition_date.strftime("%Y-%m-%d")
            vals.update({"document_expedition_date": document_expedition_date})
        if pms_checkin_partner_info.documentSupportNumber:
            vals.update(
                {"support_number": pms_checkin_partner_info.documentSupportNumber}
            )
        if pms_checkin_partner_info.gender:
            vals.update({"gender": pms_checkin_partner_info.gender})
        if pms_checkin_partner_info.birthdate:
            birthdate = datetime.strptime(
                pms_checkin_partner_info.birthdate, "%d/%m/%Y"
            )
            birthdate = birthdate.strftime("%Y-%m-%d")
            vals.update({"birthdate_date": birthdate})
        if pms_checkin_partner_info.residenceStreet:
            vals.update({"residence_street": pms_checkin_partner_info.residenceStreet})
        if pms_checkin_partner_info.zip:
            vals.update({"residence_zip": pms_checkin_partner_info.zip})
        if pms_checkin_partner_info.residenceCity:
            vals.update({"residence_city": pms_checkin_partner_info.residenceCity})
        if (
            pms_checkin_partner_info.nationality
            and pms_checkin_partner_info.nationality != -1
        ):
            vals.update({"nationality_id": pms_checkin_partner_info.nationality})
            vals.update({"residence_country_id": pms_checkin_partner_info.nationality})
        if (
            pms_checkin_partner_info.countryState
            and pms_checkin_partner_info.countryState != -1
        ):
            vals.update({"residence_state_id": pms_checkin_partner_info.countryState})
        return vals
