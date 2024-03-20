import logging

from odoo import _, fields
from odoo.exceptions import MissingError, ValidationError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

FORMAT_DATE = "%Y-%m-%d"


class PmsCheckinPartnerService(Component):
    _inherit = "base.rest.service"
    _name = "civitfun.checkin.partner.service"
    _usage = "guests"
    _collection = "civitfun.services"

    # ------------------------------------------------------------------------------------
    # HEAD RESERVATION--------------------------------------------------------------------
    # ------------------------------------------------------------------------------------

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("civitfun.guest.meta", is_list=False),
        output_param=Datamodel("civitfun.guest.meta.result", is_list=False),
        auth="public",
    )
    def register_hosts(self, pms_input_param):
        try:
            pms_property = (
                self.env["pms.property"]
                .sudo()
                .search(
                    [
                        ("civitfun_property_code", "=", pms_input_param.propertyId),
                        ("use_civitfun", "=", True),
                    ]
                )
            )
            if not pms_property:
                raise MissingError(_("Property not found"))
            booking_identifier = pms_input_param.bookingIdentifier.replace("-", "/")
            reservation = (
                self.env["pms.reservation"]
                .sudo()
                .search(
                    [
                        ("name", "=", booking_identifier),
                        ("pms_property_id", "=", pms_property.id),
                    ]
                )
            )
            self.check_reservation(reservation)
            checkins_response = []
            for guest in pms_input_param.guests:
                checkin_vals, partner_vals = self._mapped_hosts_info(guest)
                if guest.id:
                    checkin_partner = (
                        self.env["pms.checkin.partner"]
                        .sudo()
                        .search(
                            [
                                ("id", "=", guest.id),
                                ("reservation_id", "=", reservation.id),
                            ]
                        )
                    )
                    checkin_partner.sudo().write(checkin_vals)
                else:
                    # Check that the guest number document is not already registered
                    if reservation.checkin_partner_ids.filtered(
                        lambda x: x.document_number == guest.documentNumber
                    ):
                        raise ValidationError(
                            _("The guest with document number %s is already registered")
                            % guest.documentNumber
                        )
                    checkin_vals["reservation_id"] = reservation.id
                    checkin_partner = (
                        self.env["pms.checkin.partner"].sudo().create(checkin_vals)
                    )
                checkins_response.append(
                    {
                        "idCheckinGuest": guest.idCheckinGuest,
                        "pmsId": checkin_partner.id,
                    }
                )
                if partner_vals:
                    checkin_partner.partner_id.sudo().write(partner_vals)
            return self.env.datamodels["civitfun.guest.meta.result"](
                success=True,
                message="Guest data saved",
                guestIds=checkins_response,
            )
        except Exception as e:
            bookingResult = self.env.datamodels["civitfun.guest.meta.result"]
            return bookingResult(
                success=False,
                message=str(e),
                guestIds=[],
            )

    def _mapped_hosts_info(self, guest):
        """
        Transform a checkin partner into a civitfun.checkin.partner.info datamodel
        """
        checkin_vals = {
            "email": guest.email,
            "firstname": guest.name,
            "lastname": guest.surname,
            "lastname2": guest.secondSurname,
            "gender": self._get_mapped_gender(guest.gender),
            "birthdate_date": guest.birthDate.strftime(FORMAT_DATE),
            "nationality_id": self.env["res.country"].search(
                [
                    ("code_alpha3", "=", guest.nationality),
                ]
            ),
            "document_type": self._get_mapped_document_type(guest.documentType),
            "document_number": guest.documentNumber,
            "document_expedition_date": guest.expeditionDate.strftime(FORMAT_DATE),
            # "assigned_room": guest.assignedRoom,
            # "legal_fields": guest.legalFields,
            # "files": guest.files,
        }
        if guest.customFields.get("phone"):
            checkin_vals["phone"] = guest.customFields.get("phone")
        if guest.customFields.get("document_support_number"):
            checkin_vals["support_number"] = guest.customFields.get(
                "document_support_number"
            )
        if guest.customFields.get("documentSupportNumber"):
            checkin_vals["support_number"] = guest.customFields.get(
                "documentSupportNumber"
            )
        if guest.customFields.get("address"):
            checkin_vals["residence_street"] = guest.customFields.get(
                "address"
            ).splitlines()[0]
        res_zip = False
        if guest.customFields.get("postalCode"):
            zip_code = guest.customFields.get("postalCode")
            res_zip = self.env["res.city.zip"].search(
                [
                    ("name", "=", zip_code),
                ],
                limit=1,
            )
        if res_zip:
            checkin_vals["residence_zip"] = res_zip.name
            checkin_vals["residence_city"] = res_zip.city_id.name
            checkin_vals["residence_state_id"] = res_zip.state_id.id
            checkin_vals["residence_country_id"] = res_zip.country_id.id
        else:
            if guest.customFields.get("city"):
                checkin_vals["residence_city"] = guest.customFields.get("city")
            if guest.customFields.get("province"):
                checkin_vals["residence_state_id"] = (
                    self.env["res.country.state"]
                    .search(
                        [
                            ("code", "=", guest.customFields.get("province")),
                        ]
                    )
                    .id
                )
            if guest.customFields.get("country"):
                checkin_vals["residence_country_id"] = (
                    self.env["res.country"]
                    .search(
                        [
                            ("code_alpha3", "=", guest.customFields.get("country")),
                        ]
                    )
                    .id
                )

        # partner_vals = {
        #     "lang": self._get_mapped_lang(guest.lang),
        # }
        partner_vals = {}
        return checkin_vals, partner_vals

    def check_reservation(self, reservation):
        if not reservation:
            raise MissingError(_("Reservation not found"))
        if reservation.state in ["cancel"]:
            raise MissingError(_("Reservation cancelled"))
        if reservation.state in ["done"] or reservation.checkout < fields.Date.today():
            raise MissingError(_("Reservation already checked out"))

    def _get_mapped_lang(self, lang):
        pms_lang = (
            self.env["res.lang"]
            .sudo()
            .search(
                [
                    ("iso_code", "=", lang),
                ]
            )
        )
        return pms_lang.code or False

    def _get_mapped_gender(self, gender):
        if gender == "M":
            return "male"
        if gender == "F":
            return "female"
        return "other"

    def _get_mapped_document_type(self, document_type):
        document_category = (
            self.env["res.partner.id_category"]
            .sudo()
            .search(
                [
                    ("civitfun_category", "=", document_type),
                ]
            )
        )
        if not document_category:
            raise MissingError(
                _("Document type not found, please check the pms configuration")
            )
        return document_category
