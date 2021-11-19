# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsService(models.Model):
    _name = "pms.service"
    _description = "Property Service"

    name = fields.Many2one(
        string="Service",
        help="Service",
        required=True,
        comodel_name="product.product",
        ondelete="restrict",
        domain="[('type', '=', 'service')]",
    )
    active = fields.Boolean(
        string="Active", help="Determines if service is active", default=True
    )
    sequence = fields.Integer(
        string="Sequence",
        help="Field used to change the position of the rooms in tree view."
        "Changing the position changes the sequence",
        default=0,
    )
    property_id = fields.Many2one(
        string="Property",
        required=True,
        comodel_name="pms.property",
        ondelete="restrict",
    )
    vendor_id = fields.Many2one(
        string="Vendor", required=True, comodel_name="res.partner", ondelete="restrict"
    )
    icon = fields.Char(
        string="Website Icon", help="Set Icon name from https://fontawesome.com/"
    )
