import base64
import tempfile
import os
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


from odoo import _
from odoo.odoo.exceptions import MissingError


class PmsRoomTypeClassService(Component):
    _inherit = "base.rest.service"
    _name = "pms.user.service"
    _usage = "users"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/<int:user_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.api.rest.user.output", is_list=False),
        auth="jwt_api_pms",
    )

    def get_user(self, user_id):
        user = self.env["res.users"].sudo().search([("id", "=", user_id)])
        if user:
            PmsUserInfo = self.env.datamodels["pms.api.rest.user.output"]
            return PmsUserInfo(
                userId=user.id,
                userName=user.name,
                userEmail=user.email if user.email else "",
                userPhone=user.phone if user.phone else "",
                userImageBase64=user.image_1920 if user.image_1920 else "",
                isNewInterfaceUser=user.is_new_interface_app_user,
            )

        else:
            raise MissingError(_("Folio not found"))

    @restapi.method(
        [
            (
                [
                    "/p/<int:user_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.api.rest.user.output", is_list=False),
        auth="jwt_api_pms",
    )
    def write_user(self, user_id, input_data):
        user = self.env["res.users"].sudo().search([("id", "=", user_id)])
        if user:
            if input_data.isNewInterfaceUser is not None:
                user.write(
                    {
                        "is_new_interface_app_user": input_data.isNewInterfaceUser,
                    }
                )
            user.write(
                {
                    "name": input_data.userName,
                    "email": input_data.userEmail,
                    "phone": input_data.userPhone,
                }
            )
            if input_data.userImageBase64 is not None:
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    f.write(base64.b64decode(input_data.userImageBase64))
                    temp_path = f.name

                with open(temp_path, "rb") as f:
                    user_image = f.read()
                os.unlink(temp_path)

                user.write(
                    {
                        "image_1024": base64.b64encode(user_image),
                    }
                )
            else:
                user.write(
                    {
                        "image_1024": '',
                    }
                )
            return True

