import time

import werkzeug.exceptions
from jose import jwt

from odoo import _
from odoo.exceptions import AccessDenied

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import url_image_pms_api_rest


class PmsLoginService(Component):
    _inherit = "base.rest.service"
    _name = "pms.auth.service"
    _usage = "login"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.api.rest.user.input", is_list=False),
        output_param=Datamodel("pms.api.rest.user.output", is_list=False),
        auth="public",
        cors="*",
    )
    def login(self, user):
        user_record = (
            self.env["res.users"].sudo().search([("login", "=", user.username)])
        )
        # formula = ms_now + 24 hours
        timestamp_expire_in_a_sec = int(time.time()) + 24 * 60 * 60

        if not user_record:
            raise werkzeug.exceptions.Unauthorized(_("wrong user/pass"))
        try:
            user_record.with_user(user_record)._check_credentials(user.password, None)
        except AccessDenied:
            raise werkzeug.exceptions.Unauthorized(_("wrong user/pass"))

        validator = (
            self.env["auth.jwt.validator"].sudo()._get_validator_by_name("api_pms")
        )
        assert len(validator) == 1

        PmsApiRestUserOutput = self.env.datamodels["pms.api.rest.user.output"]

        token = jwt.encode(
            {
                "aud": "api_pms",
                "iss": "pms",
                "exp": timestamp_expire_in_a_sec,
                "username": user.username,
            },
            key=validator.secret_key,
            algorithm=validator.secret_algorithm,
        )
        avail_rule_names = []
        for avail_field in user_record.availability_rule_field_ids:
            avail_rule_names.append(avail_field.name)

        return PmsApiRestUserOutput(
            token=token,
            expirationDate=timestamp_expire_in_a_sec,
            userId=user_record.id,
            userName=user_record.name,
            userFirstName=user_record.firstname or None,
            userEmail=user_record.email or None,
            userPhone=user_record.phone or None,
            defaultPropertyId=user_record.pms_property_id.id,
            defaultPropertyName=user_record.pms_property_id.name,
            userImageBase64=user_record.partner_id.image_1024
            if user_record.partner_id.image_1024
            else None,
            userImageUrl=url_image_pms_api_rest(
                "res.partner", user_record.partner_id.id, "image_1024"
            ),
            isNewInterfaceUser=user_record.is_new_interface_app_user,
            availabilityRuleFields=avail_rule_names,
        )
