from werkzeug.exceptions import BadRequest

from odoo import fields, models, _


class PmsFolio(models.Model):
    _inherit = "pms.folio"
    api_rest_id = fields.Char(string="API Rest ID", help="API Rest ID")

    pms_api_log_ids = fields.Many2many(
        string="API Logs",
        help="API Logs",
        comodel_name="pms.api.log",
        relation="pms_folio_pms_api_log_rel",
        column1="folio_ids",
        column2="pms_api_log_ids",
    )

    def build_reservations_cmds(self, folio_record, pms_folio_info):
        cmds = []
        existing_reservation_ids = []
        for reservation in pms_folio_info.reservations:

            # search for existing service line
            reservation_record = self.env["pms.reservation"].search([("id", "=", reservation.id)])

            # initialize vals
            reservation_vals = {}

            # add to existing reservation ids
            if reservation_record:
                existing_reservation_ids.append(reservation_record.id)

            # checkin
            if reservation.checkin is not None:
                if (
                        not reservation_record or reservation.checkin != str(reservation_record.checkin)
                ):
                    reservation_vals.update({"checkin": reservation.checkin})

            # checkout
            if reservation.checkout is not None:
                if not reservation_record or reservation.checkout != str(reservation_record.checkout):
                    reservation_vals.update({"checkout": reservation.checkout})

            # reservationType
            if reservation.reservationType is not None:
                if not reservation_record or reservation.reservationType != reservation_record.reservation_type:
                    reservation_vals.update({"reservation_type": reservation.reservationType})
            else:
                if pms_folio_info.reservationType is not None:
                    if not reservation_record or pms_folio_info.reservationType != reservation_record.reservation_type:
                        reservation_vals.update({"reservation_type": pms_folio_info.reservationType})

            # roomTypeId
            if reservation.roomTypeId is not None:
                if not reservation_record or reservation.roomTypeId != reservation_record.room_type_id.id:
                    reservation_vals.update({"room_type_id": reservation.roomTypeId})

            # partnerId
            if reservation.partnerId is not None:
                if not reservation_record or reservation.partnerId != reservation_record.partner_id.id:
                    reservation_vals.update({"partner_id": reservation.partnerId})
            else:
                if pms_folio_info.partnerId is not None:
                    if not reservation_record or pms_folio_info.partnerId != reservation_record.partner_id.id:
                        reservation_vals.update({"partner_id": pms_folio_info.partnerId})

            # preconfirm
            if pms_folio_info.preconfirm is not None:
                if not reservation_record or pms_folio_info.preconfirm != reservation_record.preconfirm:
                    reservation_vals.update({"preconfirm": pms_folio_info.preconfirm})

            # adults
            if reservation.adults is not None:
                if not reservation_record or reservation.adults != reservation_record.adults:
                    reservation_vals.update({"adults": reservation.adults})

            # children
            if reservation.children is not None:
                if not reservation_record or reservation.children != reservation_record.children:
                    reservation_vals.update({"children": reservation.children})

            # pricelistId
            if reservation.pricelistId is not None:
                if not reservation_record or reservation.pricelistId != reservation_record.pricelist_id.id:
                    reservation_vals.update({"pricelist_id": reservation.pricelistId})
            else:
                if pms_folio_info.pricelistId is not None:
                    if not reservation_record or pms_folio_info.pricelistId != reservation_record.pricelist_id.id:
                        reservation_vals.update({"pricelist_id": pms_folio_info.pricelistId})

            # board_service_room_id
            if reservation.boardServiceId is not None:
                if not reservation_record or reservation.boardServiceId != reservation_record.board_service_room_id.id:
                    reservation_vals.update(
                        {
                            "board_service_room_id": reservation.boardServiceId if (
                                    reservation.boardServiceId != 0
                            ) else False
                        }
                    )

            # reservation_lines
            if reservation.reservationLines is not None:
                cmds_reservation_lines = self.env['pms.reservation'].build_reservation_lines_cmds(
                    reservation_record,
                    reservation.reservationLines
                )
                if cmds_reservation_lines:
                    reservation_vals.update({"reservation_line_ids": cmds_reservation_lines})

            # service_ids
            cmds_service_ids = self.env['pms.reservation'].build_reservation_services_cmds(
                reservation_record,
                reservation.services if reservation.services else [],
                reservation.boardServiceId if reservation.boardServiceId else False,
            )
            if cmds_service_ids:
                reservation_vals.update({"service_ids": cmds_service_ids})

            # add reservations t
            if reservation_vals:
                if reservation_record:
                    cmds.append((1, reservation_record.id, reservation_vals))
                else:
                    cmds.append((0, 0, reservation_vals))

        # detect if the folio has reservations which are not in the request
        if folio_record and folio_record.reservation_ids.filtered(
                lambda x: x.id not in existing_reservation_ids and x.state != 'cancel'
        ):
            raise BadRequest(_("Removing reservations is not allowed"))
        return cmds

    def build_creation_update_services_cmds(self, services):
        cmds = []
        existing_service_ids = []
        for service in services:
            # search for existing service
            service_record = self.env["pms.service"].search(
                [
                    ("id", "=", service.id)
                ]
            )
            # if service exists add to existing_service_ids
            if service_record:
                existing_service_ids.append(service_record.id)

            # initialize vals
            service_vals = {}

            # product_id
            if service.productId is not None:
                if not service_record or service.productId != service_record.product_id.id:
                    service_vals.update({"product_id": service.productId})
            # name
            if service.name is not None:
                if not service_record or service.name != service_record.name:
                    service_vals.update({"name": service.name})

            # isBoardService
            if service.isBoardService is not None:
                if not service_record or service.isBoardService != service_record.is_board_service:
                    service_vals.update({"is_board_service": service.isBoardService})

            # serviceLines
            if service.serviceLines is not None:
                cmds_service_lines = self.build_service_lines_cmds(
                    service_record,
                    service.serviceLines
                )
                if cmds_service_lines:
                    service_vals.update({"service_line_ids": cmds_service_lines})
                service_vals.update({"no_auto_add_lines": True})

            # add reservation to modify/create cmds
            if service_vals:
                if service_record:
                    cmds.append((1, service_record.id, service_vals))
                else:
                    cmds.append((0, 0, service_vals))

        return cmds, existing_service_ids

    def build_services_cmds(self, folio_record, services):
        cmds, existing_service_ids = self.build_creation_update_services_cmds(services)

        # iterate existing services to remove the ones not in the request
        for service_to_remove in folio_record.service_ids.filtered(
                lambda x: x.id not in existing_service_ids and not x.reservation_id
        ):
            cmds.append((2, service_to_remove.id))
        return cmds

    def build_service_lines_cmds(self, service_record, service_lines):
        cmds = []
        existing_service_line_ids = []
        for service_line in service_lines:
            service_line_record = False
            if service_record:
                # search for existing service line
                service_line_record = self.env["pms.service.line"].search(
                    [
                        ("date", "=", service_line.date),
                        ("service_id", "=", service_record.id)
                    ]
                )
            # if service line exists add to existing services lines
            if service_line_record:
                existing_service_line_ids.append(service_line_record.id)

            # initialize vals
            service_line_vals = {}

            # date
            if service_line.date is not None:
                if not service_line_record or service_line.date != str(service_line_record.date):
                    service_line_vals.update({"date": service_line.date})

            # priceUnit
            if service_line.priceUnit is not None:
                if not service_line_record or round(service_line.priceUnit, 2) != round(service_line_record.price_unit, 2):
                    service_line_vals.update({"price_unit": service_line.priceUnit})

            # discount
            if service_line.discount is not None:
                if not service_line_record or round(service_line.discount, 2) != round(service_line_record.discount, 2):
                    service_line_vals.update({"discount": service_line.discount})

            # quantity
            if service_line.quantity is not None:
                if not service_line_record or service_line.quantity != service_line_record.day_qty:
                    service_line_vals.update({"day_qty": service_line.quantity})

            # add service line to modify/create cmds
            if service_line_vals:
                if not service_line_record:
                    cmds.append((0, 0, service_line_vals))
                else:
                    cmds.append((1, service_line_record.id, service_line_vals))

        # iterate existing service lines to remove the ones not in the request
        if service_record:
            for service_line_to_remove in service_record.service_line_ids.filtered(
                    lambda x: x.id not in existing_service_line_ids
            ):
                cmds.append((2, service_line_to_remove.id))
        return cmds

    def create_folio_vals(self, folio_record, pms_folio_info):

        # init vals
        folio_vals = {}

        # pmsPropertyId
        if pms_folio_info.pmsPropertyId is not None:
            if not folio_record or pms_folio_info.pmsPropertyId != folio_record.pms_property_id.id:
                folio_vals.update({"pms_property_id": pms_folio_info.pmsPropertyId})

        # pricelistId
        if pms_folio_info.pricelistId is not None:
            if not folio_record or pms_folio_info.pricelistId != folio_record.pricelist_id.id:
                folio_vals.update({"pricelist_id": pms_folio_info.pricelistId})

        # reservationType
        if pms_folio_info.reservationType is not None:
            if not folio_record or pms_folio_info.reservationType != folio_record.reservation_type:
                folio_vals.update({"reservation_type": pms_folio_info.reservationType})

        # partnerId
        if pms_folio_info.partnerId is not None:
            if not folio_record or pms_folio_info.partnerId != folio_record.partner_id.id:
                folio_vals.update({"partner_id": pms_folio_info.partnerId})

        # partnerName
        if pms_folio_info.partnerName is not None:
            if not folio_record or pms_folio_info.partnerName != folio_record.partner_name:
                folio_vals.update({"partner_name": pms_folio_info.partnerName})

        # partnerEmail
        if pms_folio_info.partnerEmail is not None:
            if not folio_record or pms_folio_info.partnerEmail != folio_record.email:
                folio_vals.update({"email": pms_folio_info.partnerEmail})

        # partnerPhone
        if pms_folio_info.partnerPhone is not None:
            if not folio_record or pms_folio_info.partnerPhone != folio_record.mobile:
                folio_vals.update({"mobile": pms_folio_info.partnerPhone})

        # language
        if pms_folio_info.language is not None:
            lang = (
                    self.env["res.lang"].search([("iso_code", "=", pms_folio_info.language)], limit=1).code
                    or pms_folio_info.language
            )
            if not folio_record or lang != folio_record.lang:
                folio_vals.update({"lang": lang})

        # saleChannelId
        if pms_folio_info.saleChannelId is not None:
            if not folio_record or pms_folio_info.saleChannelId != folio_record.channel_type_id.id:
                folio_vals.update({"sale_channel_origin_id": pms_folio_info.saleChannelId})

        # agencyId
        if pms_folio_info.agencyId is not None:
            if not folio_record or pms_folio_info.agencyId != folio_record.agency_id.id:
                folio_vals.update({"agency_id": pms_folio_info.agencyId})

        # externalReference
        if pms_folio_info.externalReference is not None:
            if not folio_record or pms_folio_info.externalReference != folio_record.external_reference:
                folio_vals.update({"external_reference": pms_folio_info.externalReference})

        # internalComment
        if pms_folio_info.internalComment is not None:
            if not folio_record or pms_folio_info.internalComment != folio_record.internal_comment:
                folio_vals.update({"internal_comment": pms_folio_info.internalComment})

        # closureReasonId
        if pms_folio_info.closureReasonId is not None:
            if not folio_record or pms_folio_info.closureReasonId != folio_record.closure_reason_id.id:
                folio_vals.update({"closure_reason_id": pms_folio_info.closureReasonId})

        # outOfServiceDescription
        if pms_folio_info.outOfServiceDescription is not None:
            if not folio_record or pms_folio_info.outOfServiceDescription != folio_record.out_of_service_description:
                folio_vals.update({"out_service_description": pms_folio_info.outOfServiceDescription})

        # reservation_ids
        if pms_folio_info.reservations is not None:
            cmds_reservations = self.env['pms.folio'].build_reservations_cmds(folio_record, pms_folio_info)
            if cmds_reservations:
                folio_vals.update({"reservation_ids": cmds_reservations})

        # folio service_ids
        if pms_folio_info.services is not None:
            cmds_services_folio = self.env['pms.folio'].build_services_cmds(folio_record, pms_folio_info.services)
            if cmds_services_folio:
                folio_vals.update({"service_ids": cmds_services_folio})

        return folio_vals
