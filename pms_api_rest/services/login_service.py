import time

from jose import jwt

from odoo import _
from odoo.exceptions import ValidationError, AccessDenied, UserError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPartnerService(Component):
    _inherit = "base.rest.service"
    _name = "pms.auth.service"
    _usage = "login"
    _collection = "pms.public.services"

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
        # output_param=Datamodel("pms.api.rest.user.output", is_list=False),
    )
    def aa(self, user):

        user_record = (
            self.env["res.users"].sudo().search([("login", "=", user.username)])
        )

        if not user_record:
            ValidationError(_("user or password not valid"))
        try:
            user_record.with_user(user_record)._check_credentials(user.password, None)

        except Exception as e:
            raise UserError("")

        PmsApiRestUserOutput = self.env.datamodels["pms.api.rest.user.output"]
        expiration_date = time.time() + 36660
        token = jwt.encode(
            {
                "aud": "api_pms",
                "iss": "pms",
                "exp": expiration_date,
                "username": user.username,
                "password": user.password,
            },
            key="pms_secret_key_example",
            algorithm=jwt.ALGORITHMS.HS256,
        )
        # return PmsApiRestUserOutput(token=token)
        return token

    def user_error(self):
        """
        Simulate an odoo.exceptions.UserError
        Should be translated into BadRequest with a description into the json
        body
        """
        raise UserError(_("UserError message"))

    # Validator
    def _validator_user_error(self):
        return {}

    def _validator_return_user_error(self):
        return {}

    def _validator_validation_error(self):
        return {}

    def _validator_return_validation_error(self):
        return {}

    def _validator_session_expired(self):
        return {}

    def _validator_return_session_expired(self):
        return {}

    def _validator_missing_error(self):
        return {}

    def _validator_return_missing_error(self):
        return {}

    def _validator_access_error(self):
        return {}

    def _validator_return_access_error(self):
        return {}

    def _validator_access_denied(self):
        return {}

    def _validator_return_access_denied(self):
        return {}

    def _validator_http_exception(self):
        return {}

    def _validator_return_http_exception(self):
        return {}

    def _validator_bare_exception(self):
        return {}

    def _validator_return_bare_exception(self):
        return {}
