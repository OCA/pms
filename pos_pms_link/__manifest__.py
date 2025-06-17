##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2022 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "POS PMS link",
    "summary": "Allows to use PMS reservations on the POS interface",
    "version": "16.0.1.0.0",
    "author": "Comunitea Servicios Tecnológicos S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pms",
    "license": "AGPL-3",
    "category": "Point of Sale",
    "depends": [
        "point_of_sale",
        "pms",
        "pos_hr",
    ],
    "data": [
        # "views/assets_common.xml",
        "views/pms_service_line.xml",
        "views/pos_order.xml",
        "views/res_config_settings.xml",
    ],
    "demo": [],
    "assets": {
        "point_of_sale.assets": [
            "pos_pms_link/static/src/js/*.js",
            "pos_pms_link/static/src/js/*/*.js",
            "pos_pms_link/static/src/js/*/*/*.js",
            "pos_pms_link/static/src/xml/*.xml",
            "pos_pms_link/static/src/xml/*/*.xml",
            "pos_pms_link/static/src/xml/*/*/*.xml",
            "pos_pms_link/static/src/scss/*.scss",
        ],
    },
    "installable": True,
}
