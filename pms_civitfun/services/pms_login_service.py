import time

import werkzeug.exceptions
from jose import jwt

from odoo import _

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class CivitfunLoginService(Component):
    _inherit = "base.rest.service"
    _name = "civitfun.auth.service"
    _usage = "login"
    _collection = "civitfun.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("civitfun.api.rest.user.input", is_list=False),
        output_param=Datamodel("civitfun.api.rest.user.output", is_list=False),
        auth="public",
        cors="*",
    )
    def login(self, user):
        property_code = user.propertyId

        pms_property = (
            self.env["pms.property"]
            .sudo()
            .search(
                [
                    ("civitfun_property_code", "=", property_code),
                    ("use_civitfun", "=", True),
                ]
            )
        )
        if not pms_property:
            raise werkzeug.exceptions.Unauthorized(_("wrong property"))

        validator = (
            self.env["auth.jwt.validator"].sudo()._get_validator_by_name("civitfun")
        )
        assert len(validator) == 1
        # formula = ms_now + ms in 1 sec * secs in 1 min
        minutes = 10000
        timestamp_expire_in_a_min = int(time.time() * 1000.0) + 1000 * 60 * minutes

        CivitfunApiRestUserOutput = self.env.datamodels["civitfun.api.rest.user.output"]

        token = jwt.encode(
            {
                "aud": "civitfun",
                "iss": "civitfun",
                "exp": timestamp_expire_in_a_min,
                "publicKey": "civitfun_public_key_example",
                "email": validator.static_user_id.email,
            },
            key=validator.secret_key,
            algorithm=validator.secret_algorithm,
        )

        return CivitfunApiRestUserOutput(
            status="success",
            message="login success",
            token=token,
        )
