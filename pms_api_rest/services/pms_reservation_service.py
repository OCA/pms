from datetime import datetime, timedelta

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
        if pms_search_param.pms_property_id:
            domain.append(("pms_property_id", "=", pms_search_param.pms_property_id))
        reservation = self.env["pms.reservation"].search(domain)
        res = []
        PmsReservationInfo = self.env.datamodels["pms.reservation.info"]
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
            res = PmsReservationInfo(
                id=reservation.id,
                partner=reservation.partner_id.name if reservation.partner_id else "",
                checkin=str(reservation.checkin),
                checkout=str(reservation.checkout),
                preferredRoomId=reservation.preferred_room_id.id
                if reservation.preferred_room_id
                else 0,
                preferredRoomName=reservation.preferred_room_id.name
                if reservation.preferred_room_id
                else "",
                roomTypeId=reservation.room_type_id.id
                if reservation.room_type_id
                else 0,
                roomTypeName=reservation.room_type_id.name
                if reservation.room_type_id
                else "",
                name=reservation.name,
                priceTotal=reservation.price_room_services_set,
                priceOnlyServices=reservation.price_services
                if reservation.price_services
                else 0.0,
                priceOnlyRoom=reservation.price_total,
                pricelistName=reservation.pricelist_id.name
                if reservation.pricelist_id
                else "",
                pricelistId=reservation.pricelist_id.id
                if reservation.pricelist_id
                else 0,
                services=services if services else [],
                messages=messages,
                boardServiceId=reservation.board_service_room_id.id
                if reservation.board_service_room_id
                else 0,
                boardServiceName=reservation.board_service_room_id.pms_board_service_id.name
                if reservation.board_service_room_id
                else "",
                # review if its an agency
                channelTypeId=reservation.channel_type_id.id
                if reservation.channel_type_id
                else 0,
                adults=reservation.adults,
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

            reservation_to_update.write(reservation_vals)

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_id>/checkinpartners",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.search.param"),
        output_param=Datamodel("pms.checkin.partner.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_checkin_partners(self, reservation_id, pms_search_param):
        domain = list()
        domain.append(("id", "=", reservation_id))
        domain.append(("pms_property_id", "=", pms_search_param.pms_property_id))
        reservation = self.env["pms.reservation"].search(domain)
        checkin_partners = []
        PmsCheckinPartnerInfo = self.env.datamodels["pms.checkin.partner.info"]
        if not reservation:
            pass
        else:
            for checkin_partner in reservation.checkin_partner_ids:
                checkin_partners.append(
                    PmsCheckinPartnerInfo(
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
