from odoo import fields, models


class PmsDoor(models.Model):
    _name = "pms.door"
    _description = "Door"

    name = fields.Char(string="Door Name")
    room_id = fields.Many2one(comodel_name="pms.room", string="Room", required=True)
    noukee_id = fields.Char(string="Noukee Door Id")
