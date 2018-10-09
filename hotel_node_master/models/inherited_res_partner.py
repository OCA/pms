# Copyright 2018  Pablo Q. Barriuso
# Copyright 2018  Alexandre Díaz
# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'
    # As res.partner has already a `user_ids` field, you can not use that name in this inheritance
    node_user_ids = fields.One2many('hotel.node.user', 'partner_id',
                                    'Users associated to this partner')
