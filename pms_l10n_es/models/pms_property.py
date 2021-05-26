import time

import requests
from bs4 import BeautifulSoup as bs

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.modules import get_module_resource


class PmsProperty(models.Model):
    _inherit = "pms.property"

    institution = fields.Selection(
        [
            ("guardia_civil", "Guardia Civil"),
            ("policia_nacional", "Policía Nacional (soon)"),
            ("ertxaintxa", "Ertxaintxa (soon)"),
            ("mossos", "Mossos_d'esquadra (soon)"),
        ],
        string="Institution",
        default="guardia_civil",
        help="Institution to send daily guest data.",
    )
    institution_property_id = fields.Char(
        string="Institution property id",
        size=10,
        help="Id provided by institution to send data from property.",
    )
    institution_user = fields.Char(
        string="Institution user", help="User provided by institution to send the data."
    )
    institution_password = fields.Char(
        string="Institution password",
        help="Password provided by institution to send the data.",
    )

    def test_gc_connection(self):
        for pms_property in self:
            if (
                pms_property.institution == "guardia_civil"
                and pms_property.institution_property_id
                and pms_property.institution_user
                and pms_property.institution_password
            ):

                url = "https://hospederias.guardiacivil.es/"
                login_route = "/hospederias/login.do"
                logout_route = "/hospederias/logout.do"

                headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 "
                    "Build/MRA58N) AppleWebKit/537.36 (KHTML, like "
                    "Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36",
                }
                session = requests.session()
                login_payload = {
                    "usuario": pms_property.institution_user,
                    "pswd": pms_property.institution_password,
                }

                # login
                response_login = session.post(
                    url + login_route,
                    headers=headers,
                    data=login_payload,
                    verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                )
                time.sleep(1)
                # logout
                session.get(
                    url + logout_route,
                    headers=headers,
                    verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                )
                session.close()

                # check if authentication was successful / unsuccessful or the
                # resource cannot be accessed
                soup = bs(response_login.text, "html.parser")
                errors = soup.select("#txterror > ul > li")
                if errors:
                    raise ValidationError(errors[0].text)
                else:
                    login_correct = soup.select(".cabecera2")
                    if login_correct:
                        message = {
                            "type": "ir.actions.client",
                            "tag": "display_notification",
                            "params": {
                                "title": _("Connection Established!"),
                                "message": _("Connection established succesfully"),
                                "sticky": False,
                            },
                        }
                        return message
                    else:
                        raise ValidationError(_("Connection could not be established"))
