# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2021 Eric Antones <eantones@nuobit.com>
# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsRoomType(models.Model):
    _name = "pms.room.type"
    _description = "Room Type"

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer(string="Sequence", default=0)
    icon = fields.Char(
        string="Website Icon", help="Set Icon name from https://fontawesome.com/"
    )
