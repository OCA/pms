# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_room_type = fields.Boolean('Is a Room Type', default=False)
    # iscategid = fields.Boolean('Is categ id')
    # isservice = fields.Boolean('Is Service id')
