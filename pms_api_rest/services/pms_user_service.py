import base64
import tempfile
import os
import werkzeug.exceptions

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from odoo.exceptions import AccessDenied
from datetime import datetime, timedelta



from odoo import _
from odoo.exceptions import MissingError


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
                userFirstName=user.firstname if user.firstname else "",
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

    @restapi.method(
        [
            (
                [
                    "/p/<int:user_id>/change-password",
                ],
                "PATCH",
            )
        ],
        output_param=Datamodel("pms.api.rest.user.login.output", is_list=False),
        input_param=Datamodel("pms.api.rest.user.input", is_list=False),
        auth="jwt_api_pms",
    )
    def change_password(self, user_id, input_data):
        user = self.env["res.users"].sudo().search([("id", "=", user_id)])
        if user:
            try:
                user.with_user(user)._check_credentials(input_data.password, None)
            except AccessDenied:
                raise werkzeug.exceptions.Unauthorized(_("Wrong password"))


            user.change_password(input_data.password, input_data.newPassword)

            PmsUserInfo = self.env.datamodels["pms.api.rest.user.login.output"]
            return PmsUserInfo(
                login=user.login,
            )

    @restapi.method(
        [
            (
                [
                    "/p/reset-password",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.api.rest.user.input", is_list=False),
        auth="public",
        cors="*",
    )
    def reset_password(self, input_data):
        values = {
            "password": input_data.password,
        }
        self.env["res.users"].sudo().signup(values, input_data.resetToken)
        return True


    @restapi.method(
        [
            (
                [
                    "/send-mail-reset-password",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.api.rest.user.input", is_list=False),
        auth="public",
        cors="*",
    )
    def send_mail_to_reset_password(self, input_data):
        user = self.env["res.users"].sudo().search([("email", "=", input_data.userEmail)])
        if user:
            template_id = self.env.ref("pms_api_rest.pms_reset_password_email").id
            template = self.env['mail.template'].sudo().browse(template_id)
            if not template:
                return False
            expiration_datetime = datetime.now() + timedelta(minutes=15)
            user.partner_id.sudo().signup_prepare(expiration=expiration_datetime)
            template.with_context({'app_url': input_data.url}).send_mail(user.id, force_send=True)
            return True
        return False


    @restapi.method(
        [
            (
                [
                    "/check-reset-password-token/<string:reset_token>",
                ],
                "GET",
            )
        ],
        auth="public",
        cors="*",
    )
    def check_reset_password_token(self, reset_token):
        user = self.env["res.partner"].sudo().search([("signup_token", "=", reset_token)])
        is_token_expired = False
        if not user:
            return True
        if user.sudo().signup_expiration < datetime.now():
            is_token_expired = True
        return is_token_expired
