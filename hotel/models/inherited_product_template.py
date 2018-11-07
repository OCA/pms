# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_hotel_service = fields.Boolean('Is a Hotel Service', default=False)
    per_day = fields.Boolean('Unit increment per day')
    per_person = fields.Boolean('Unit increment per person')
    daily_limit = fields.Integer('Daily limit')
