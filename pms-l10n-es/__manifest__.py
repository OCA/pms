# Copyright 2013 Nicolas Bessi (Camptocamp SA)
# Copyright 2014 Agile Business Group (<http://www.agilebg.com>)
# Copyright 2015 Grupo ESOC (<http://www.grupoesoc.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Adaptation to spanish law",
    "version": "14.0.1.0.0",
    "author": "CommitSun, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "category": "Localization",
    "website": "https://github.com/OCA/pms",
    "depends": [
        "pms",
        "partner_firstname",
        "partner_second_lastname",
        "partner_contact_gender",
        "partner_contact_birthdate",
    ],
    "data": [
        "views/pms_checkin_partner_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
