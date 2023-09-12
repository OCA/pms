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
    _name = "civitfun.checkin.partner.service"
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
                        ("name", "=", booking_identifier),
                        ("pms_property_id", "=", pms_property.id),
                    ]
                )
            )
            self.check_reservation(reservation)
        except Exception as e:
            civitfunPaymentInfo = self.env["civitfun.payment.info"]
            return civitfunPaymentInfo(
                success=False,
                message=str(e),
                accountIds=[],
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
