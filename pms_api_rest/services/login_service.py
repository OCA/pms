import time

from jose import jwt

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPartnerService(Component):
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
    )
    def login(self, user):

        user_record = (
            self.env["res.users"].sudo().search([("login", "=", user.username)])
        )

        if not user_record:
            raise ValidationError(_("user or password not valid"))
        user_record.with_user(user_record)._check_credentials(user.password, None)
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
        return PmsApiRestUserOutput(token=token)
