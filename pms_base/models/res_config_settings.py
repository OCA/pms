# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Groups
    group_pms_show_amenity = fields.Boolean(
        string="Show Amenities", implied_group="pms_base.group_pms_show_amenity"
    )
    group_pms_show_room = fields.Boolean(
        string="Show Rooms", implied_group="pms_base.group_pms_show_room"
    )
    group_pms_show_service = fields.Boolean(
        string="Show Services", implied_group="pms_base.group_pms_show_service"
    )
    group_pms_show_team = fields.Boolean(
        string="Show Teams", implied_group="pms_base.group_pms_show_team"
    )

    # Modules
    module_pms_account = fields.Boolean(string="Manage Accounting")
    module_pms_account_asset = fields.Boolean(string="Manage Assets")
    module_pms_contract = fields.Boolean(string="Manage Contracts")
    module_pms_crm = fields.Boolean(string="Link a property to a lead")
    module_pms_project = fields.Boolean(string="Link to Projects and Tasks")
    module_pms_purchase = fields.Boolean(string="Link to Purchases")
    module_pms_sale = fields.Boolean(string="Manage Reservations")
    module_pms_stock = fields.Boolean(string="Manage Content")
    module_pms_website = fields.Boolean(string="Publish properties")
    module_pms_website_sale = fields.Boolean(string="Allow online booking")
    module_connector_guesty = fields.Boolean(string="Connect with Guesty")
    module_connector_wubook = fields.Boolean(string="Connect with Wubook")

    # Companies
    pms_uom = fields.Selection(
        string="Unit of Measure", related="company_id.pms_uom", readonly=False
    )
