from werkzeug.exceptions import BadRequest

from odoo import _, fields, models


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

    def _compare_simple_field(self, record, field, new_value, transform=str):
        if not record:
            return True
        return transform(getattr(record, field, None)) != transform(new_value)

    def _compare_field_ids(self, record_field, new_id):
        current_id = record_field.id if record_field else None
        return new_id != current_id

    def _build_core_fields_vals(self, reservation, reservation_record, pms_folio_info):
        vals = {}
        if reservation.checkin is not None and self._compare_simple_field(
            reservation_record, "checkin", reservation.checkin
        ):
            vals["checkin"] = reservation.checkin
        if reservation.checkout is not None and self._compare_simple_field(
            reservation_record, "checkout", reservation.checkout
        ):
            vals["checkout"] = reservation.checkout
        reservation_type = reservation.reservationType or pms_folio_info.reservationType
        if reservation_type is not None and self._compare_simple_field(
            reservation_record, "reservation_type", reservation_type
        ):
            vals["reservation_type"] = reservation_type
        if pms_folio_info.preconfirm is not None and (
            not reservation_record
            or pms_folio_info.preconfirm != reservation_record.preconfirm
        ):
            vals["preconfirm"] = pms_folio_info.preconfirm
        return vals

    def _build_person_vals(self, reservation, reservation_record, pms_folio_info):
        vals = {}
        partner_id = reservation.partnerId or pms_folio_info.partnerId
        if partner_id is not None:
            if not reservation_record or self._compare_field_ids(
                reservation_record.partner_id, partner_id
            ):
                vals["partner_id"] = partner_id
        if reservation.adults is not None and (
            not reservation_record or reservation.adults != reservation_record.adults
        ):
            vals["adults"] = reservation.adults
        if reservation.children is not None and (
            not reservation_record
            or reservation.children != reservation_record.children
        ):
            vals["children"] = reservation.children
        return vals

    def _build_product_vals(self, reservation, reservation_record, pms_folio_info):
        vals = {}
        if reservation.roomTypeId is not None:
            if not reservation_record or self._compare_field_ids(
                reservation_record.room_type_id, reservation.roomTypeId
            ):
                vals["room_type_id"] = reservation.roomTypeId
        pricelist_id = reservation.pricelistId or pms_folio_info.pricelistId
        if pricelist_id is not None:
            if not reservation_record or self._compare_field_ids(
                reservation_record.pricelist_id, pricelist_id
            ):
                vals["pricelist_id"] = pricelist_id
        if reservation.boardServiceId is not None:
            if not reservation_record or self._compare_field_ids(
                reservation_record.board_service_room_id, reservation.boardServiceId
            ):
                vals["board_service_room_id"] = (
                    reservation.boardServiceId
                    if reservation.boardServiceId != 0
                    else False
                )
        return vals

    def _build_subrecords_vals(self, reservation, reservation_record):
        vals = {}
        if reservation.reservationLines:
            cmds_lines = self.env["pms.reservation"].build_reservation_lines_cmds(
                reservation_record, reservation.reservationLines
            )
            if cmds_lines:
                vals["reservation_line_ids"] = cmds_lines
        cmds_service_ids = self.env["pms.reservation"].build_reservation_services_cmds(
            reservation_record,
            reservation.services or [],
            reservation.boardServiceId or False,
        )
        if cmds_service_ids:
            vals["service_ids"] = cmds_service_ids
        return vals

    def _build_reservation_vals(self, reservation, reservation_record, pms_folio_info):
        vals = {}
        vals.update(
            self._build_core_fields_vals(
                reservation, reservation_record, pms_folio_info
            )
        )
        vals.update(
            self._build_person_vals(reservation, reservation_record, pms_folio_info)
        )
        vals.update(
            self._build_product_vals(reservation, reservation_record, pms_folio_info)
        )
        vals.update(self._build_subrecords_vals(reservation, reservation_record))
        return vals

    def build_reservations_cmds(self, folio_record, pms_folio_info):
        cmds = []
        existing_reservation_ids = []

        for reservation in pms_folio_info.reservations:
            reservation_record = self.env["pms.reservation"].search(
                [("id", "=", reservation.id)]
            )
            if reservation_record:
                existing_reservation_ids.append(reservation_record.id)

            vals = self._build_reservation_vals(
                reservation, reservation_record, pms_folio_info
            )
            if vals:
                cmds.append(
                    (1, reservation_record.id, vals)
                    if reservation_record
                    else (0, 0, vals)
                )

        if folio_record and folio_record.reservation_ids.filtered(
            lambda x: x.id not in existing_reservation_ids and x.state != "cancel"
        ):
            raise BadRequest(_("Removing reservations is not allowed"))

        return cmds

    def build_creation_update_services_cmds(self, services):
        cmds = []
        existing_service_ids = []
        for service in services:
            # search for existing service
            service_record = self.env["pms.service"].search([("id", "=", service.id)])
            # if service exists add to existing_service_ids
            if service_record:
                existing_service_ids.append(service_record.id)

            # initialize vals
            service_vals = {}

            # product_id
            if service.productId is not None:
                if (
                    not service_record
                    or service.productId != service_record.product_id.id
                ):
                    service_vals.update({"product_id": service.productId})
            # name
            if service.name is not None:
                if not service_record or service.name != service_record.name:
                    service_vals.update({"name": service.name})

            # isBoardService
            if service.isBoardService is not None:
                if (
                    not service_record
                    or service.isBoardService != service_record.is_board_service
                ):
                    service_vals.update({"is_board_service": service.isBoardService})

            # serviceLines
            if service.serviceLines is not None:
                cmds_service_lines = self.build_service_lines_cmds(
                    service_record, service.serviceLines
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
                        ("service_id", "=", service_record.id),
                    ]
                )
            # if service line exists add to existing services lines
            if service_line_record:
                existing_service_line_ids.append(service_line_record.id)

            # initialize vals
            service_line_vals = {}

            # date
            if service_line.date is not None:
                if not service_line_record or service_line.date != str(
                    service_line_record.date
                ):
                    service_line_vals.update({"date": service_line.date})

            # priceUnit
            if service_line.priceUnit is not None:
                if not service_line_record or round(service_line.priceUnit, 2) != round(
                    service_line_record.price_unit, 2
                ):
                    service_line_vals.update({"price_unit": service_line.priceUnit})

            # discount
            if service_line.discount is not None:
                if not service_line_record or round(service_line.discount, 2) != round(
                    service_line_record.discount, 2
                ):
                    service_line_vals.update({"discount": service_line.discount})

            # quantity
            if service_line.quantity is not None:
                if (
                    not service_line_record
                    or service_line.quantity != service_line_record.day_qty
                ):
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
        folio_vals = {}

        def update(field_name, record_attr, key=None, transform=lambda x: x):
            key = key or record_attr
            incoming_value = getattr(pms_folio_info, field_name)
            if incoming_value is not None:
                existing_value = (
                    getattr(folio_record, record_attr, None) if folio_record else None
                )
                if transform(incoming_value) != transform(existing_value):
                    folio_vals[key] = incoming_value

        update("pmsPropertyId", "pms_property_id")
        update("pricelistId", "pricelist_id")
        update("reservationType", "reservation_type")
        update("partnerId", "partner_id")
        update("partnerName", "partner_name")
        update("partnerEmail", "email")
        update("partnerPhone", "mobile")
        update("saleChannelId", "channel_type_id", "sale_channel_origin_id")
        update("agencyId", "agency_id")
        update("externalReference", "external_reference")
        update("internalComment", "internal_comment")
        update("closureReasonId", "closure_reason_id")
        update(
            "outOfServiceDescription",
            "out_of_service_description",
            "out_service_description",
        )

        # language (special case)
        if pms_folio_info.language:
            lang_obj = self.env["res.lang"].search(
                [("iso_code", "=", pms_folio_info.language)], limit=1
            )
            lang = lang_obj.code if lang_obj else pms_folio_info.language
            if not folio_record or lang != folio_record.lang:
                folio_vals["lang"] = lang

        # reservation_ids
        if pms_folio_info.reservations:
            cmds_reservations = self.env["pms.folio"].build_reservations_cmds(
                folio_record, pms_folio_info
            )
            if cmds_reservations:
                folio_vals["reservation_ids"] = cmds_reservations

        # service_ids
        if pms_folio_info.services:
            cmds_services_folio = self.env["pms.folio"].build_services_cmds(
                folio_record, pms_folio_info.services
            )
            if cmds_services_folio:
                folio_vals["service_ids"] = cmds_services_folio

        return folio_vals
