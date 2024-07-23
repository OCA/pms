from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsReservationLineService(Component):
    _inherit = "base.rest.service"
    _name = "pms.reservation.line.service"
    _usage = "reservation-lines"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/<int:reservation_line_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.reservation.line.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_reservation_line(self, reservation_line_id):
        reservation_line = self.env["pms.reservation.line"].search(
            [("id", "=", reservation_line_id)]
        )
        if reservation_line:
            PmsReservationLineInfo = self.env.datamodels["pms.reservation.line.info"]
            return PmsReservationLineInfo(
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
        else:
            raise MissingError(_("Reservation Line not found"))

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.reservation.line.search.param", is_list=False),
        output_param=Datamodel("pms.reservation.line.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_reservation_lines(self, pms_reservation_lines_search_param):
        result = []
        if (
            pms_reservation_lines_search_param.dateFrom
            and pms_reservation_lines_search_param.dateTo
            and pms_reservation_lines_search_param.pmsPropertyId
        ):
            date_from = datetime.strptime(
                pms_reservation_lines_search_param.dateFrom, "%Y-%m-%d"
            ).date()
            date_to = datetime.strptime(
                pms_reservation_lines_search_param.dateTo, "%Y-%m-%d"
            ).date()

            domain = [
                ("date", ">=", date_from),
                ("date", "<", date_to),
                (
                    "pms_property_id",
                    "=",
                    pms_reservation_lines_search_param.pmsPropertyId,
                ),
            ]
            PmsReservationLineInfo = self.env.datamodels["pms.reservation.line.info"]
            for reservation_line in self.env["pms.reservation.line"].search(domain):
                print(reservation_line.state)
                result.append(
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
                        reservationType=reservation_line.reservation_id.reservation_type,
                        state=reservation_line.state,
                        isSplitted=reservation_line.reservation_id.splitted,
                    )
                )
        return result

    # @restapi.method(
    #     [
    #         (
    #             [
    #                 "/",
    #             ],
    #             "GET",
    #         )
    #     ],
    #     input_param=Datamodel("pms.reservation.line.search.param"),
    #     output_param=Datamodel("pms.reservation.line.info", is_list=True),
    #     auth="jwt_api_pms",
    # )
    # def get_reservation_lines(self, reservation_lines_search_param):
    #     domain = []
    #     if reservation_lines_search_param.date:
    #         domain.append(("date", "=", reservation_lines_search_param.date))
    #     if reservation_lines_search_param.reservationId:
    #         domain.append(
    #             ("reservation_id", "=", reservation_lines_search_param.reservationId)
    #         )
    #     if reservation_lines_search_param.pmsPropertyId:
    #         domain.extend(
    #             [
    #                 (
    #                     "pms_property_id",
    #                     "=",
    #                     reservation_lines_search_param.pmsPropertyId,
    #                 ),
    #             ]
    #         )

    #     result_lines = []
    #     PmsReservationLineInfo = self.env.datamodels["pms.reservation.line.info"]
    #     for reservation_line in self.env["pms.reservation.line"].search(
    #         domain,
    #     ):
    #         result_lines.append(
    #             PmsReservationLineInfo(
    #                 id=reservation_line.id,
    #                 date=datetime.combine(
    #                     reservation_line.date, datetime.min.time()
    #                 ).isoformat(),
    #                 price=round(reservation_line.price, 2),
    #                 discount=round(reservation_line.discount, 2),
    #                 cancelDiscount=round(reservation_line.cancel_discount, 2),
    #                 roomId=reservation_line.room_id.id,
    #                 reservationId=reservation_line.reservation_id.id,
    #                 pmsPropertyId=reservation_line.pms_property_id.id,
    #             )
    #         )
    #     return result_lines

    @restapi.method(
        [
            (
                [
                    "/p/<int:reservation_line_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.reservation.line.info"),
        auth="jwt_api_pms",
    )
    def update_reservation_line(self, reservation_line_id, reservation_line_info):
        reservation_line = self.env["pms.reservation.line"].search(
            [("id", "=", reservation_line_id)]
        )
        vals = dict()
        if reservation_line:
            if reservation_line_info.price is not None:
                vals["price"] = reservation_line_info.price
            if reservation_line_info.discount is not None:
                vals["discount"] = reservation_line_info.discount
            if reservation_line_info.cancelDiscount is not None:
                vals["cancel_discount"] = reservation_line_info.cancelDiscount
            if reservation_line_info.roomId:
                vals["room_id"] = reservation_line_info.roomId
            if reservation_line_info.isReselling is not None:
                vals["is_reselling"] = reservation_line_info.isReselling
            reservation_line.write(vals)
        else:
            raise MissingError(_("Reservation Line not found"))
