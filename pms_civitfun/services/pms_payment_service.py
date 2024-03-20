import logging

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

FORMAT_DATE = "%Y-%m-%d"


class PmsPaymentnService(Component):
    _inherit = "base.rest.service"
    _name = "civitfun.payment.service"
    _usage = "payment"
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
        input_param=Datamodel("civitfun.payment.register", is_list=False),
        output_param=Datamodel("civitfun.payment.info", is_list=False),
        auth="public",
    )
    def payment_register(self, pms_input_param):
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
                        "&",
                        ("pms_property_id", "=", pms_property.id),
                        "|",
                        ("name", "=", booking_identifier),
                        ("folio_id.name", "=", booking_identifier),
                    ],
                    limit=1,
                )
            )
            if not reservation:
                raise MissingError(_("Reservation not found"))
            folio = reservation.folio_id
            pending_amount = folio.pending_amount
            if pending_amount <= 0:
                raise MissingError(_("Not pending amount"))
            folio.do_payment(
                journal=pms_property.civitfun_payment_journal_id,
                receivable_account=pms_property.civitfun_payment_journal_id.suspense_account_id,
                user=self.env.user,
                amount=pending_amount,
                folio=folio,
            )
            civitfunPaymentInfo = self.env.datamodels["civitfun.payment.info"]
            return civitfunPaymentInfo(
                success=True,
                message="Payment registered.",
            )
        except Exception as e:
            civitfunPaymentInfo = self.env.datamodels["civitfun.payment.info"]
            return civitfunPaymentInfo(
                success=False,
                message=str(e),
                accounts=[],
            )

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

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("civitfun.payment.search", is_list=False),
        output_param=Datamodel("civitfun.payment.info", is_list=False),
        auth="public",
    )
    def payment_search(self, pms_input_param):
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
                        "&",
                        ("pms_property_id", "=", pms_property.id),
                        "|",
                        ("name", "=", booking_identifier),
                        ("folio_id.name", "=", booking_identifier),
                    ],
                    limit=1,
                )
            )
            if not reservation:
                raise MissingError(_("Reservation not found"))
            folio = reservation.folio_id
            pending_amount = folio.pending_amount
            civitfunPaymentInfo = self.env.datamodels["civitfun.payment.info"]
            return civitfunPaymentInfo(
                success=True,
                message="",
                currency="EUR",
                accounts=[
                    {
                        "id": str(folio.id),
                        "description": folio.name,
                        "amount": pending_amount,
                        "charges": [
                            {
                                "id": folio.id,
                                "concept": folio.name,
                                "amount": pending_amount,
                            }
                        ],
                    }
                ],
            )
        except Exception as e:
            civitfunPaymentInfo = self.env.datamodels["civitfun.payment.info"]
            return civitfunPaymentInfo(
                success=False,
                message=str(e),
                accounts=[],
            )
