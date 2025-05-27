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

    def _should_update(self, record, field, new_value, transform=lambda x: x):
        return not record or transform(getattr(record, field)) != transform(new_value)

    def _build_optional_field(
        self, rec, res, field_name, odoo_field, vals, transform=lambda x: x
    ):
        value = getattr(res, field_name)
        if value is not None and self._should_update(rec, odoo_field, value, transform):
            vals[odoo_field] = value

    def _build_fallback_field(
        self,
        rec,
        res,
        fallback_obj,
        field_name,
        odoo_field,
        vals,
        transform=lambda x: x,
    ):
        value = getattr(res, field_name) or getattr(fallback_obj, field_name)
        if value is not None and self._should_update(rec, odoo_field, value, transform):
            vals[odoo_field] = value

    def build_reservations_cmds(self, folio_record, pms_folio_info):
        cmds = []
        existing_reservation_ids = []

        for res in pms_folio_info.reservations:
            rec = self.env["pms.reservation"].search([("id", "=", res.id)])
            vals = {}

            if rec:
                existing_reservation_ids.append(rec.id)

            self._build_optional_field(rec, res, "checkin", "checkin", vals, str)
            self._build_optional_field(rec, res, "checkout", "checkout", vals, str)
            self._build_fallback_field(
                rec, res, pms_folio_info, "reservationType", "reservation_type", vals
            )
            self._build_optional_field(
                rec, res, "roomTypeId", "room_type_id", vals, lambda x: x.id if x else x
            )
            self._build_fallback_field(
                rec,
                res,
                pms_folio_info,
                "partnerId",
                "partner_id",
                vals,
                lambda x: x.id if x else x,
            )
            self._build_optional_field(
                rec, pms_folio_info, "preconfirm", "preconfirm", vals
            )
            self._build_optional_field(rec, res, "adults", "adults", vals)
            self._build_optional_field(rec, res, "children", "children", vals)
            self._build_fallback_field(
                rec,
                res,
                pms_folio_info,
                "pricelistId",
                "pricelist_id",
                vals,
                lambda x: x.id if x else x,
            )

            if res.boardServiceId is not None and self._should_update(
                rec,
                "board_service_room_id",
                res.boardServiceId,
                lambda x: x.id if x else 0,
            ):
                vals["board_service_room_id"] = res.boardServiceId or False

            if res.reservationLines:
                cmds_lines = self.env["pms.reservation"].build_reservation_lines_cmds(
                    rec, res.reservationLines
                )
                if cmds_lines:
                    vals["reservation_line_ids"] = cmds_lines

            cmds_services = self.env["pms.reservation"].build_reservation_services_cmds(
                rec,
                res.services or [],
                res.boardServiceId or False,
            )
            if cmds_services:
                vals["service_ids"] = cmds_services

            if vals:
                cmds.append((1, rec.id, vals) if rec else (0, 0, vals))

        if folio_record and folio_record.reservation_ids.filtered(
            lambda r: r.id not in existing_reservation_ids and r.state != "cancel"
        ):
            raise BadRequest(_("Removing reservations is not allowed"))

        return cmds

    def create_folio_vals(self, folio_record, pms_folio_info):
        folio_vals = {}

        def update(field, key=None, transform=lambda x: x):
            value = getattr(pms_folio_info, field)
            if value is not None and self._should_update(
                folio_record, key or field, value, transform
            ):
                folio_vals[key or field] = value

        update(
            "pmsPropertyId",
            "pms_property_id",
            lambda x: x.id if hasattr(x, "id") else x,
        )
        update("pricelistId", "pricelist_id", lambda x: x.id if hasattr(x, "id") else x)
        update("reservationType", "reservation_type")
        update("partnerId", "partner_id", lambda x: x.id if hasattr(x, "id") else x)
        update("partnerName", "partner_name")
        update("partnerEmail", "email")
        update("partnerPhone", "mobile")

        if pms_folio_info.language:
            lang_obj = self.env["res.lang"].search(
                [("iso_code", "=", pms_folio_info.language)], limit=1
            )
            lang = lang_obj.code if lang_obj else pms_folio_info.language
            if self._should_update(folio_record, "lang", lang):
                folio_vals["lang"] = lang

        update(
            "saleChannelId",
            "sale_channel_origin_id",
            lambda x: x.id if hasattr(x, "id") else x,
        )
        update("agencyId", "agency_id", lambda x: x.id if hasattr(x, "id") else x)
        update("externalReference", "external_reference")
        update("internalComment", "internal_comment")
        update(
            "closureReasonId",
            "closure_reason_id",
            lambda x: x.id if hasattr(x, "id") else x,
        )
        update("outOfServiceDescription", "out_service_description")

        if pms_folio_info.reservations:
            cmds_reservations = self.build_reservations_cmds(
                folio_record, pms_folio_info
            )
            if cmds_reservations:
                folio_vals["reservation_ids"] = cmds_reservations

        if pms_folio_info.services:
            cmds_services = self.build_services_cmds(
                folio_record, pms_folio_info.services
            )
            if cmds_services:
                folio_vals["service_ids"] = cmds_services

        return folio_vals

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
