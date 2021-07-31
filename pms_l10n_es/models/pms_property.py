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
            ("policia_nacional", "Policía Nacional"),
            ("ertxaintxa", "Ertxaintxa (soon)"),
            ("mossos", "Mossos_d'esquadra (soon)"),
        ],
        string="Institution",
        default="guardia_civil",
        help="Institution to send daily guest data.",
    )
    institution_property_id = fields.Char(
        string="Institution property id",
        help="Id provided by institution to send data from property.",
    )
    institution_user = fields.Char(
        string="Institution user", help="User provided by institution to send the data."
    )
    institution_password = fields.Char(
        string="Institution password",
        help="Password provided by institution to send the data.",
    )
    ine_tourism_number = fields.Char(
        "Tourism number",
        help="Registration number in the Ministry of Tourism. Used for INE statistics.",
    )
    ine_seats = fields.Integer(
        "Beds available excluding extra beds",
        default=0,
        help="Used for INE statistics.",
    )
    ine_permanent_staff = fields.Integer(
        "Permanent Staff", default=0, help="Used for INE statistics."
    )
    ine_eventual_staff = fields.Integer(
        "Eventual Staff", default=0, help="Used for INE statistics."
    )
    ine_unpaid_staff = fields.Integer(
        "Unpaid Staff", default=0, help="Used for INE statistics."
    )
    ine_category_id = fields.Many2one(
        "pms.ine.tourism.type.category",
        help="Hotel category in the Ministry of Tourism. Used for INE statistics.",
    )

    def test_connection(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 "
            "Build/MRA58N) AppleWebKit/537.36 (KHTML, like "
            "Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36",
        }
        for record in self:
            if (
                record.institution == "guardia_civil"
                and record.institution_property_id
                and record.institution_user
                and record.institution_password
            ):
                url = "https://hospederias.guardiacivil.es/"
                login_route = "/hospederias/login.do"
                logout_route = "/hospederias/logout.do"
                session = requests.session()
                login_payload = {
                    "usuario": record.institution_user,
                    "pswd": record.institution_password,
                }
                # login
                response_login = session.post(
                    url + login_route,
                    headers=headers,
                    data=login_payload,
                    verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                )
                time.sleep(0.1)
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
            elif (
                record.institution == "policia_nacional"
                and record.institution_property_id
                and record.institution_user
                and record.institution_password
            ):
                url = "https://webpol.policia.es/e-hotel"
                pre_login_route = "/login"
                login_route = "/execute_login"
                home_route = "/inicio"
                logout_route = "/execute_logout"
                session = requests.session()
                response_pre_login = session.post(
                    url + pre_login_route,
                    headers=headers,
                    verify=False,
                )
                soup = bs(response_pre_login.text, "html.parser")
                token = soup.select("input[name='_csrf']")[0]["value"]
                time.sleep(0.1)
                login_payload = {
                    "username": record.institution_user,
                    "password": record.institution_password,
                    "_csrf": token,
                }
                session.post(
                    url + login_route,
                    headers=headers,
                    data=login_payload,
                    verify=False,
                )
                time.sleep(0.1)
                response_home = session.get(
                    url + home_route,
                    headers=headers,
                    verify=False,
                )
                soup = bs(response_home.text, "html.parser")
                login_correct = soup.select("#datosUsuarioBanner")
                if login_correct:
                    session.post(
                        url + logout_route,
                        headers=headers,
                        verify=False,
                        data={"_csrf": token},
                    )

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
